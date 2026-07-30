from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from fastapi import APIRouter, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import AdminUser, CurrentUser, DbSession, PaginationDep, TeacherUser
from app.core.exceptions import NotFoundError, ValidationError
from app.models.catalog import Course
from app.models.commerce import Coupon, Order, PayoutRequest
from app.models.enums import OrderStatus
from app.modules.commerce.schemas import (
    AddToCartRequest,
    CartItemView,
    CartSummary,
    CheckoutRequest,
    CheckoutResponse,
    CouponCreate,
    CouponValidateRequest,
    CouponValidateResponse,
    CouponView,
    EarningsPoint,
    EarningsSummary,
    OrderView,
    PaymentView,
    PayoutRequestCreate,
    PayoutRequestView,
)
from app.modules.commerce.service import (
    CartService,
    CheckoutService,
    CouponService,
    EarningsService,
)
from app.modules.courses.mappers import to_course_card
from app.schemas.common import Message, Page

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Commerce"])

ZERO = Decimal("0")


@router.get("/cart", response_model=CartSummary, summary="Savat")
async def get_cart(user: CurrentUser, db: DbSession) -> CartSummary:
    items = await CartService(db).list_items(user)
    views = [
        CartItemView(id=item.id, course=to_course_card(item.course), created_at=item.created_at)
        for item in items
    ]
    subtotal = sum((item.course.effective_price for item in items), ZERO)
    return CartSummary(items=views, subtotal=subtotal, total=subtotal)


@router.post(
    "/cart",
    response_model=CartSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Savatga qo'shish",
)
async def add_to_cart(payload: AddToCartRequest, user: CurrentUser, db: DbSession) -> CartSummary:
    service = CartService(db)
    await service.add(user, payload.course_id)
    return await get_cart(user, db)


@router.delete("/cart/{course_id}", response_model=CartSummary, summary="Savatdan olib tashlash")
async def remove_from_cart(course_id: uuid.UUID, user: CurrentUser, db: DbSession) -> CartSummary:
    await CartService(db).remove(user, course_id)
    return await get_cart(user, db)


@router.delete("/cart", response_model=Message, summary="Savatni bo'shatish")
async def clear_cart(user: CurrentUser, db: DbSession) -> Message:
    await CartService(db).clear(user)
    return Message(message="Savat bo'shatildi")


@router.post(
    "/cart/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="To'lovga o'tish",
)
async def checkout(payload: CheckoutRequest, user: CurrentUser, db: DbSession) -> CheckoutResponse:
    order, payment, checkout_url = await CheckoutService(db).checkout(user, payload)
    return CheckoutResponse(
        order=OrderView.model_validate(order),
        checkout_url=checkout_url,
        provider=payment.provider,
        payment_id=payment.id,
        is_free=order.total <= ZERO,
    )


@router.get("/orders", response_model=Page[OrderView], summary="Buyurtmalarim")
async def my_orders(user: CurrentUser, db: DbSession, pagination: PaginationDep) -> Page[OrderView]:
    stmt = select(Order).where(Order.user_id == user.id).options(selectinload(Order.items))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(Order.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    )
    return Page.build(
        [OrderView.model_validate(o) for o in rows.all()],
        total,
        pagination.page,
        pagination.per_page,
    )


@router.get("/orders/{order_id}", response_model=OrderView, summary="Buyurtma tafsiloti")
async def get_order(order_id: uuid.UUID, user: CurrentUser, db: DbSession) -> OrderView:
    order = await db.scalar(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user.id)
        .options(selectinload(Order.items))
    )
    if order is None:
        raise NotFoundError("Buyurtma topilmadi")
    return OrderView.model_validate(order)


@router.get(
    "/orders/{order_id}/payments", response_model=list[PaymentView], summary="Buyurtma to'lovlari"
)
async def order_payments(
    order_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> list[PaymentView]:
    order = await db.scalar(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user.id)
        .options(selectinload(Order.payments))
    )
    if order is None:
        raise NotFoundError("Buyurtma topilmadi")
    return [PaymentView.model_validate(p) for p in order.payments]


@router.post("/payments/webhook/payme", summary="Payme webhook (JSON-RPC)")
async def payme_webhook(request: Request, db: DbSession) -> dict:
    payload = await request.json()
    return await CheckoutService(db).handle_webhook("payme", payload, dict(request.headers))


@router.post("/payments/webhook/click", summary="Click webhook (Prepare/Complete)")
async def click_webhook(request: Request, db: DbSession) -> dict:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
    else:
        payload = dict(await request.form())
    return await CheckoutService(db).handle_webhook("click", payload, dict(request.headers))


@router.post("/payments/webhook/mock", summary="Mock to'lov webhook (sandbox)")
async def mock_webhook(request: Request, db: DbSession) -> dict:
    payload = await request.json()
    return await CheckoutService(db).handle_webhook("mock", payload, dict(request.headers))


@router.post(
    "/coupons/validate", response_model=CouponValidateResponse, summary="Kuponni tekshirish"
)
async def validate_coupon(
    payload: CouponValidateRequest, user: CurrentUser, db: DbSession
) -> CouponValidateResponse:
    course_ids = payload.course_ids
    if not course_ids:
        items = await CartService(db).list_items(user)
        courses = [item.course for item in items]
    else:
        courses = list((await db.scalars(select(Course).where(Course.id.in_(course_ids)))).all())

    if not courses:
        raise ValidationError("Savat bo'sh — kuponni qo'llash uchun kurs tanlang")

    subtotal = sum((c.effective_price for c in courses), ZERO)
    coupon, discount, message = await CouponService(db).validate(payload.code, courses, subtotal)
    return CouponValidateResponse(
        valid=coupon is not None,
        discount=discount,
        message=message,
        coupon=CouponView.model_validate(coupon) if coupon else None,
    )


@router.post(
    "/teacher/coupons",
    response_model=CouponView,
    status_code=status.HTTP_201_CREATED,
    summary="Kupon yaratish (teacher)",
)
async def create_coupon(payload: CouponCreate, user: TeacherUser, db: DbSession) -> CouponView:
    coupon = await CouponService(db).create(user, payload)
    return CouponView.model_validate(coupon)


@router.get("/teacher/coupons", response_model=Page[CouponView], summary="Kuponlarim")
async def my_coupons(
    user: TeacherUser, db: DbSession, pagination: PaginationDep
) -> Page[CouponView]:
    stmt = select(Coupon).where(Coupon.owner_id == user.id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(Coupon.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    )
    return Page.build(
        [CouponView.model_validate(c) for c in rows.all()],
        total,
        pagination.page,
        pagination.per_page,
    )


@router.delete("/teacher/coupons/{coupon_id}", response_model=Message, summary="Kuponni o'chirish")
async def delete_coupon(coupon_id: uuid.UUID, user: TeacherUser, db: DbSession) -> Message:
    coupon = await db.scalar(
        select(Coupon).where(Coupon.id == coupon_id, Coupon.owner_id == user.id)
    )
    if coupon is None:
        raise NotFoundError("Kupon topilmadi")
    coupon.is_active = False
    await db.commit()
    return Message(message="Kupon o'chirildi")


@router.get("/teacher/earnings", response_model=EarningsSummary, summary="Daromad xulosasi")
async def earnings_summary(user: TeacherUser, db: DbSession) -> EarningsSummary:
    return EarningsSummary(**await EarningsService(db).summary(user))


@router.get(
    "/teacher/earnings/chart", response_model=list[EarningsPoint], summary="Daromad grafigi"
)
async def earnings_chart(user: TeacherUser, db: DbSession, days: int = 30) -> list[EarningsPoint]:
    points = await EarningsService(db).timeseries(user, days=min(days, 365))
    return [EarningsPoint(**point) for point in points]


@router.post(
    "/teacher/payouts",
    response_model=PayoutRequestView,
    status_code=status.HTTP_201_CREATED,
    summary="Pul yechish so'rovi",
)
async def request_payout(
    payload: PayoutRequestCreate, user: TeacherUser, db: DbSession
) -> PayoutRequestView:
    summary = await EarningsService(db).summary(user)
    available = summary["net_total"] - summary["paid_out"] - summary["pending_payout"]
    if payload.amount > available:
        raise ValidationError(f"Yechish uchun mavjud summa: {available}")

    payout = PayoutRequest(
        user_id=user.id,
        organization_id=user.organization_id,
        amount=payload.amount,
        payout_details=payload.payout_details,
    )
    db.add(payout)
    await db.commit()
    await db.refresh(payout)
    return PayoutRequestView.model_validate(payout)


@router.get(
    "/teacher/payouts", response_model=Page[PayoutRequestView], summary="Payout so'rovlarim"
)
async def my_payouts(
    user: TeacherUser, db: DbSession, pagination: PaginationDep
) -> Page[PayoutRequestView]:
    stmt = select(PayoutRequest).where(PayoutRequest.user_id == user.id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(PayoutRequest.requested_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    return Page.build(
        [PayoutRequestView.model_validate(p) for p in rows.all()],
        total,
        pagination.page,
        pagination.per_page,
    )


@router.get(
    "/admin/finance/orders", response_model=Page[OrderView], summary="Barcha buyurtmalar (admin)"
)
async def admin_orders(
    _: AdminUser,
    db: DbSession,
    pagination: PaginationDep,
    order_status: OrderStatus | None = None,
) -> Page[OrderView]:
    stmt = select(Order).options(selectinload(Order.items))
    if order_status is not None:
        stmt = stmt.where(Order.status == order_status)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(Order.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    )
    return Page.build(
        [OrderView.model_validate(o) for o in rows.all()],
        total,
        pagination.page,
        pagination.per_page,
    )


@router.get(
    "/admin/finance/payouts",
    response_model=Page[PayoutRequestView],
    summary="Payout so'rovlari (admin)",
)
async def admin_payouts(
    _: AdminUser,
    db: DbSession,
    pagination: PaginationDep,
    payout_status: str | None = None,
) -> Page[PayoutRequestView]:
    stmt = select(PayoutRequest)
    if payout_status:
        stmt = stmt.where(PayoutRequest.status == payout_status)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(PayoutRequest.requested_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    return Page.build(
        [PayoutRequestView.model_validate(p) for p in rows.all()],
        total,
        pagination.page,
        pagination.per_page,
    )


@router.patch(
    "/admin/finance/payouts/{payout_id}",
    response_model=PayoutRequestView,
    summary="Payout so'rovini tasdiqlash/rad etish",
)
async def review_payout(
    payout_id: uuid.UUID,
    admin: AdminUser,
    db: DbSession,
    new_status: str,
    comment: str | None = None,
) -> PayoutRequestView:
    if new_status not in {"approved", "paid", "rejected"}:
        raise ValidationError("Status: approved | paid | rejected")

    payout = await db.scalar(select(PayoutRequest).where(PayoutRequest.id == payout_id))
    if payout is None:
        raise NotFoundError("So'rov topilmadi")

    from datetime import UTC, datetime

    payout.status = new_status
    payout.admin_comment = comment
    payout.reviewed_by_id = admin.id
    payout.reviewed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(payout)
    return PayoutRequestView.model_validate(payout)
