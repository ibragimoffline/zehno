from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, PaymentError, ValidationError
from app.core.security import generate_code
from app.integrations.factory import get_payment_provider
from app.integrations.payment.base import InvoiceRequest, WebhookResult
from app.models.catalog import Course
from app.models.commerce import CartItem, Coupon, Order, OrderItem, Payment
from app.models.enums import (
    CourseStatus,
    EnrollmentSource,
    EnrollmentStatus,
    OrderStatus,
    PaymentStatus,
)
from app.models.learning import Enrollment
from app.models.user import User
from app.modules.commerce.schemas import CheckoutRequest, CouponCreate

logger = logging.getLogger(__name__)

ZERO = Decimal("0")


def _money(value: Decimal | int | float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CartService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_items(self, user: User) -> list[CartItem]:
        rows = await self.db.scalars(
            select(CartItem)
            .where(CartItem.user_id == user.id)
            .options(
                selectinload(CartItem.course).selectinload(Course.owner),
                selectinload(CartItem.course).selectinload(Course.category),
            )
            .order_by(CartItem.created_at.desc())
        )
        return list(rows.all())

    async def add(self, user: User, course_id: uuid.UUID) -> CartItem:
        course = await self.db.scalar(
            select(Course).where(Course.id == course_id, Course.status == CourseStatus.published)
        )
        if course is None:
            raise NotFoundError("Kurs topilmadi yoki nashr etilmagan")

        already = await self.db.scalar(
            select(Enrollment.id).where(
                Enrollment.user_id == user.id, Enrollment.course_id == course_id
            )
        )
        if already:
            raise ConflictError("Bu kurs allaqachon sizda mavjud")

        existing = await self.db.scalar(
            select(CartItem).where(CartItem.user_id == user.id, CartItem.course_id == course_id)
        )
        if existing:
            return existing

        item = CartItem(user_id=user.id, course_id=course_id)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item, ["course"])
        return item

    async def remove(self, user: User, course_id: uuid.UUID) -> None:
        item = await self.db.scalar(
            select(CartItem).where(CartItem.user_id == user.id, CartItem.course_id == course_id)
        )
        if item is None:
            raise NotFoundError("Savatda bunday kurs yo'q")
        await self.db.delete(item)
        await self.db.commit()

    async def clear(self, user: User, course_ids: list[uuid.UUID] | None = None) -> None:
        stmt = select(CartItem).where(CartItem.user_id == user.id)
        if course_ids:
            stmt = stmt.where(CartItem.course_id.in_(course_ids))
        for item in (await self.db.scalars(stmt)).all():
            await self.db.delete(item)
        await self.db.commit()


class CouponService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, owner: User, payload: CouponCreate) -> Coupon:
        code = (payload.code or generate_code(8)).upper()
        if await self.db.scalar(select(Coupon.id).where(Coupon.code == code)):
            raise ConflictError("Bu kupon kodi allaqachon mavjud")

        if payload.type.value == "percent" and payload.value > 100:
            raise ValidationError("Foizli chegirma 100 dan oshmasligi kerak")

        if payload.course_id:
            course = await self.db.scalar(select(Course).where(Course.id == payload.course_id))
            if course is None:
                raise NotFoundError("Kurs topilmadi")
            if course.owner_id != owner.id and owner.role.value != "admin":
                raise ValidationError("Faqat o'z kursingizga kupon yarata olasiz")

        coupon = Coupon(code=code, owner_id=owner.id, **payload.model_dump(exclude={"code"}))
        self.db.add(coupon)
        await self.db.commit()
        await self.db.refresh(coupon)
        return coupon

    async def validate(
        self, code: str, courses: list[Course], subtotal: Decimal
    ) -> tuple[Coupon | None, Decimal, str]:
        coupon = await self.db.scalar(select(Coupon).where(Coupon.code == code.upper()))
        if coupon is None:
            return None, ZERO, "Bunday kupon topilmadi"
        if not coupon.is_active:
            return None, ZERO, "Kupon faol emas"

        now = datetime.now(UTC)
        if coupon.starts_at and coupon.starts_at > now:
            return None, ZERO, "Kupon hali faollashmagan"
        if coupon.expires_at and coupon.expires_at < now:
            return None, ZERO, "Kupon muddati tugagan"
        if coupon.max_redemptions and coupon.redemptions_count >= coupon.max_redemptions:
            return None, ZERO, "Kupondan foydalanish chegarasi tugagan"
        if coupon.min_order_total and subtotal < coupon.min_order_total:
            return None, ZERO, f"Minimal buyurtma summasi: {coupon.min_order_total}"

        base = subtotal
        if coupon.course_id:
            matched = [c for c in courses if c.id == coupon.course_id]
            if not matched:
                return None, ZERO, "Bu kupon savatdagi kurslarga tegishli emas"
            base = sum((c.effective_price for c in matched), ZERO)

        if coupon.type.value == "percent":
            discount = _money(base * coupon.value / 100)
        else:
            discount = _money(min(coupon.value, base))

        return coupon, discount, "Kupon qo'llanildi"


class CheckoutService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def checkout(self, user: User, payload: CheckoutRequest) -> tuple[Order, Payment, str]:
        courses = await self._resolve_courses(user, payload.course_ids)
        subtotal = _money(sum((c.effective_price for c in courses), ZERO))

        coupon, discount, coupon_message = (None, ZERO, "")
        if payload.coupon_code:
            coupon, discount, coupon_message = await CouponService(self.db).validate(
                payload.coupon_code, courses, subtotal
            )
            if coupon is None:
                raise ValidationError(coupon_message)

        total = _money(max(subtotal - discount, ZERO))
        commission_percent = Decimal(str(settings.PLATFORM_COMMISSION_PERCENT))

        order = Order(
            order_number=f"ZH-{datetime.now(UTC):%y%m%d}-{generate_code(6)}",
            user_id=user.id,
            organization_id=user.organization_id,
            status=OrderStatus.pending,
            subtotal=subtotal,
            discount_total=discount,
            total=total,
            coupon_id=coupon.id if coupon else None,
        )
        self.db.add(order)
        await self.db.flush()

        for course in courses:
            price = _money(course.effective_price)
            commission = _money(price * commission_percent / 100)
            self.db.add(
                OrderItem(
                    order_id=order.id,
                    course_id=course.id,
                    course_title=course.title,
                    unit_price=price,
                    seller_id=course.owner_id,
                    commission_percent=commission_percent,
                    commission_amount=commission,
                    seller_amount=_money(price - commission),
                )
            )

        if total <= ZERO:
            order.status = OrderStatus.paid
            order.paid_at = datetime.now(UTC)
            payment = Payment(
                order_id=order.id,
                provider="free",
                amount=ZERO,
                status=PaymentStatus.paid,
                paid_at=datetime.now(UTC),
            )
            self.db.add(payment)
            await self.db.commit()
            await self.fulfill_order(order.id, source=EnrollmentSource.free)
            await self.db.refresh(order, ["items"])
            return order, payment, f"{settings.PUBLIC_WEB_URL}/dashboard?order={order.order_number}"

        provider = get_payment_provider(payload.provider)
        invoice = await provider.create_invoice(
            InvoiceRequest(
                order_id=str(order.id),
                order_number=order.order_number,
                amount=total,
                currency=order.currency,
                description=", ".join(c.title for c in courses)[:200],
                return_url=payload.return_url
                or f"{settings.PUBLIC_WEB_URL}/checkout/success?order={order.order_number}",
                user_email=user.email,
                user_phone=user.phone,
            )
        )

        payment = Payment(
            order_id=order.id,
            provider=provider.provider_name,
            amount=total,
            currency=order.currency,
            status=PaymentStatus.pending,
            transaction_id=invoice.transaction_id,
            checkout_url=invoice.checkout_url,
            raw_payload=invoice.provider_meta,
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(order, ["items"])
        await self.db.refresh(payment)

        logger.info(
            "Checkout: order=%s total=%s provider=%s",
            order.order_number,
            total,
            provider.provider_name,
        )
        return order, payment, invoice.checkout_url

    async def _resolve_courses(
        self, user: User, course_ids: list[uuid.UUID] | None
    ) -> list[Course]:
        if course_ids:
            ids = list(dict.fromkeys(course_ids))
        else:
            rows = await self.db.scalars(
                select(CartItem.course_id).where(CartItem.user_id == user.id)
            )
            ids = list(rows.all())

        if not ids:
            raise ValidationError("Savat bo'sh")

        courses = list(
            (
                await self.db.scalars(
                    select(Course).where(
                        Course.id.in_(ids), Course.status == CourseStatus.published
                    )
                )
            ).all()
        )
        if len(courses) != len(ids):
            raise ValidationError("Ba'zi kurslar mavjud emas yoki nashr etilmagan")

        owned = set(
            (
                await self.db.scalars(
                    select(Enrollment.course_id).where(
                        Enrollment.user_id == user.id, Enrollment.course_id.in_(ids)
                    )
                )
            ).all()
        )
        if owned:
            raise ConflictError("Ba'zi kurslar allaqachon sizda mavjud")

        return courses

    async def handle_webhook(self, provider_name: str, payload: dict, headers: dict) -> dict:
        provider = get_payment_provider(provider_name)
        result: WebhookResult = await provider.parse_webhook(payload, headers)

        if result.order_id:
            try:
                order_uuid = uuid.UUID(str(result.order_id))
            except ValueError:
                logger.warning("Webhook: order_id noto'g'ri formatda: %s", result.order_id)
                return result.provider_response
            await self._apply_webhook(order_uuid, provider_name, result)

        return result.provider_response

    async def _apply_webhook(
        self, order_id: uuid.UUID, provider_name: str, result: WebhookResult
    ) -> None:
        order = await self.db.scalar(
            select(Order).where(Order.id == order_id).options(selectinload(Order.payments))
        )
        if order is None:
            logger.warning("Webhook: buyurtma topilmadi: %s", order_id)
            return

        payment = next(
            (p for p in order.payments if p.provider == provider_name),
            None,
        )
        if payment is None:
            payment = Payment(
                order_id=order.id,
                provider=provider_name,
                amount=order.total,
                currency=order.currency,
                status=PaymentStatus.pending,
            )
            self.db.add(payment)

        payment.status = result.status
        payment.transaction_id = result.transaction_id or payment.transaction_id
        payment.raw_payload = result.raw

        if result.status is PaymentStatus.paid:
            payment.paid_at = payment.paid_at or datetime.now(UTC)
            if order.status is not OrderStatus.paid:
                order.status = OrderStatus.paid
                order.paid_at = datetime.now(UTC)
        elif result.status is PaymentStatus.cancelled:
            order.status = OrderStatus.cancelled
            order.cancelled_at = datetime.now(UTC)
        elif result.status is PaymentStatus.failed:
            order.status = OrderStatus.failed

        await self.db.commit()

        if result.should_fulfill:
            await self.fulfill_order(order.id)

    async def fulfill_order(
        self, order_id: uuid.UUID, source: EnrollmentSource = EnrollmentSource.individual
    ) -> list[Enrollment]:
        order = await self.db.scalar(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.coupon))
        )
        if order is None:
            raise NotFoundError("Buyurtma topilmadi")
        if order.status is not OrderStatus.paid:
            raise PaymentError("Buyurtma to'lanmagan")

        created: list[Enrollment] = []
        for item in order.items:
            existing = await self.db.scalar(
                select(Enrollment).where(
                    Enrollment.user_id == order.user_id, Enrollment.course_id == item.course_id
                )
            )
            if existing:
                continue

            enrollment = Enrollment(
                user_id=order.user_id,
                course_id=item.course_id,
                order_id=order.id,
                organization_id=order.organization_id,
                source=source,
                status=EnrollmentStatus.active,
            )
            self.db.add(enrollment)
            created.append(enrollment)

            course = await self.db.scalar(select(Course).where(Course.id == item.course_id))
            if course:
                course.students_count = (course.students_count or 0) + 1

        if order.coupon:
            order.coupon.redemptions_count += 1

        course_ids = [item.course_id for item in order.items]
        for cart_item in (
            await self.db.scalars(
                select(CartItem).where(
                    CartItem.user_id == order.user_id, CartItem.course_id.in_(course_ids)
                )
            )
        ).all():
            await self.db.delete(cart_item)

        await self.db.commit()

        if created:
            _queue_post_purchase_jobs(order, created)

        logger.info("Buyurtma bajarildi: %s (+%s enrollment)", order.order_number, len(created))
        return created


def _queue_post_purchase_jobs(order: Order, enrollments: list[Enrollment]) -> None:
    try:
        from app.worker.tasks.crm import sync_enrollment_to_crm
        from app.worker.tasks.notifications import notify_payment_success

        notify_payment_success.delay(str(order.id))
        for enrollment in enrollments:
            sync_enrollment_to_crm.delay(str(enrollment.id))
    except Exception as exc:
        logger.warning("Celery job navbatga qo'yilmadi: %s", exc)


class EarningsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def summary(self, user: User) -> dict:
        row = (
            await self.db.execute(
                select(
                    func.coalesce(func.sum(OrderItem.unit_price), 0),
                    func.coalesce(func.sum(OrderItem.commission_amount), 0),
                    func.coalesce(func.sum(OrderItem.seller_amount), 0),
                    func.count(OrderItem.id),
                )
                .join(Order, OrderItem.order_id == Order.id)
                .where(OrderItem.seller_id == user.id, Order.status == OrderStatus.paid)
            )
        ).one()

        students = await self.db.scalar(
            select(func.count(func.distinct(Enrollment.user_id)))
            .join(Course, Enrollment.course_id == Course.id)
            .where(Course.owner_id == user.id)
        )

        from app.models.commerce import PayoutRequest

        paid_out = await self.db.scalar(
            select(func.coalesce(func.sum(PayoutRequest.amount), 0)).where(
                PayoutRequest.user_id == user.id, PayoutRequest.status == "paid"
            )
        )
        pending = await self.db.scalar(
            select(func.coalesce(func.sum(PayoutRequest.amount), 0)).where(
                PayoutRequest.user_id == user.id, PayoutRequest.status == "pending"
            )
        )

        net_total = _money(row[2])
        return {
            "gross_total": _money(row[0]),
            "commission_total": _money(row[1]),
            "net_total": net_total,
            "pending_payout": _money(pending or 0),
            "paid_out": _money(paid_out or 0),
            "sales_count": int(row[3] or 0),
            "students_count": int(students or 0),
        }

    async def timeseries(self, user: User, days: int = 30) -> list[dict]:
        rows = await self.db.execute(
            select(
                func.date(Order.paid_at).label("day"),
                func.coalesce(func.sum(OrderItem.unit_price), 0),
                func.coalesce(func.sum(OrderItem.seller_amount), 0),
                func.count(OrderItem.id),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .where(
                OrderItem.seller_id == user.id,
                Order.status == OrderStatus.paid,
                Order.paid_at.isnot(None),
            )
            .group_by(func.date(Order.paid_at))
            .order_by(func.date(Order.paid_at).desc())
            .limit(days)
        )
        return [
            {
                "date": str(row[0]),
                "gross": _money(row[1]),
                "net": _money(row[2]),
                "sales": int(row[3] or 0),
            }
            for row in reversed(rows.all())
        ]
