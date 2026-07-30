from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import sync_session
from app.integrations.factory import get_notification_provider
from app.integrations.notification.base import NotificationMessage
from app.models.catalog import Course
from app.models.certificate import Certificate
from app.models.commerce import Order
from app.models.enums import EnrollmentStatus, NotificationChannel, NotificationStatus
from app.models.learning import Enrollment
from app.models.organization import Organization
from app.models.system import NotificationLog
from app.models.user import User
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _send(
    db,
    user: User | None,
    template: str,
    body: str,
    *,
    subject: str | None = None,
    context: dict | None = None,
    buttons: list[dict] | None = None,
) -> bool:
    log = NotificationLog(
        user_id=user.id if user else None,
        channel=NotificationChannel.telegram,
        template=template,
        recipient=user.telegram_chat_id if user else None,
        subject=subject,
        body=body,
        context=context,
    )
    db.add(log)

    if user is None or not user.telegram_chat_id:
        log.status = NotificationStatus.failed
        log.error_message = "Telegram chat_id ulanmagan"
        db.commit()
        return False

    provider = get_notification_provider()
    try:
        sent = asyncio.run(
            provider.send(
                NotificationMessage(
                    recipient=user.telegram_chat_id,
                    body=body,
                    subject=subject,
                    buttons=buttons or [],
                )
            )
        )
        log.status = NotificationStatus.sent if sent else NotificationStatus.failed
        log.sent_at = datetime.now(UTC) if sent else None
        log.attempts = (log.attempts or 0) + 1
        if not sent:
            log.error_message = "Provayder o'chirilgan yoki sozlanmagan"
    except Exception as exc:
        log.status = NotificationStatus.failed
        log.error_message = str(exc)[:1000]
        log.attempts = (log.attempts or 0) + 1
        logger.warning("Telegram xabar yuborilmadi: %s", exc)
        db.commit()
        return False

    db.commit()
    return log.status is NotificationStatus.sent


@celery_app.task(name="app.worker.tasks.notifications.notify_payment_success")
def notify_payment_success(order_id: str) -> dict:
    with sync_session() as db:
        order = db.scalar(
            select(Order)
            .where(Order.id == uuid.UUID(order_id))
            .options(selectinload(Order.items), selectinload(Order.user))
        )
        if order is None:
            return {"skipped": "buyurtma topilmadi"}

        titles = "\n".join(f"• {item.course_title}" for item in order.items)
        body = (
            f"✅ <b>To'lov muvaffaqiyatli!</b>\n\n"
            f"Buyurtma: <code>{order.order_number}</code>\n"
            f"Summa: {order.total:,.0f} {order.currency}\n\n"
            f"Ochilgan kurslar:\n{titles}\n\n"
            f"Darslarni boshlash: {settings.PUBLIC_WEB_URL}/dashboard"
        )
        ok = _send(
            db,
            order.user,
            "payment_success",
            body,
            subject="To'lov tasdiqlandi",
            context={"order_number": order.order_number},
        )
        return {"sent": ok}


@celery_app.task(name="app.worker.tasks.notifications.notify_certificate_ready")
def notify_certificate_ready(enrollment_id: str, certificate_code: str) -> dict:
    with sync_session() as db:
        enrollment = db.scalar(
            select(Enrollment)
            .where(Enrollment.id == uuid.UUID(enrollment_id))
            .options(selectinload(Enrollment.user), selectinload(Enrollment.course))
        )
        if enrollment is None:
            return {"skipped": "enrollment topilmadi"}

        certificate = db.scalar(
            select(Certificate).where(Certificate.certificate_code == certificate_code)
        )
        body = (
            f"🎉 <b>Tabriklaymiz!</b>\n\n"
            f"«{enrollment.course.title}» kursini muvaffaqiyatli tugatdingiz.\n"
            f"Sertifikat kodi: <code>{certificate_code}</code>\n\n"
            f"Yuklab olish: {certificate.pdf_url if certificate else '-'}"
        )
        buttons = []
        if certificate and certificate.verification_url:
            buttons.append({"text": "Sertifikatni ko'rish", "url": certificate.verification_url})

        ok = _send(
            db,
            enrollment.user,
            "certificate_ready",
            body,
            subject="Sertifikat tayyor",
            context={"certificate_code": certificate_code},
            buttons=buttons,
        )
        return {"sent": ok}


@celery_app.task(name="app.worker.tasks.notifications.notify_course_moderated")
def notify_course_moderated(course_id: str, approved: bool, comment: str | None = None) -> dict:
    with sync_session() as db:
        course = db.scalar(
            select(Course)
            .where(Course.id == uuid.UUID(course_id))
            .options(selectinload(Course.owner))
        )
        if course is None:
            return {"skipped": "kurs topilmadi"}

        if approved:
            body = (
                f"✅ <b>Kursingiz tasdiqlandi!</b>\n\n"
                f"«{course.title}» endi katalogda ko'rinadi.\n"
                f"{settings.PUBLIC_WEB_URL}/courses/{course.slug}"
            )
        else:
            reason = comment or "sabab ko'rsatilmagan"
            body = (
                f"⚠️ <b>Kurs rad etildi</b>\n\n"
                f"«{course.title}»\n"
                f"Sabab: {reason}\n\n"
                f"Tahrirlab qayta yuborishingiz mumkin."
            )

        ok = _send(db, course.owner, "course_moderated", body, subject="Moderatsiya natijasi")
        return {"sent": ok}


@celery_app.task(name="app.worker.tasks.notifications.send_learning_reminders")
def send_learning_reminders() -> dict:
    with sync_session() as db:
        threshold = datetime.now(UTC) - timedelta(days=3)
        rows = db.scalars(
            select(Enrollment)
            .where(
                Enrollment.status == EnrollmentStatus.active,
                Enrollment.progress_percent < 100,
                Enrollment.updated_at < threshold,
            )
            .options(selectinload(Enrollment.user), selectinload(Enrollment.course))
            .limit(500)
        ).all()

        sent = 0
        for enrollment in rows:
            if not enrollment.user or not enrollment.user.telegram_chat_id:
                continue
            body = (
                f"📚 <b>O'qishni davom ettiramizmi?</b>\n\n"
                f"«{enrollment.course.title}» — {enrollment.progress_percent}% bajarildi.\n"
                f"Bugun 15 daqiqa vaqt ajratsangiz, keyingi darsni yakunlaysiz!\n\n"
                f"{settings.PUBLIC_WEB_URL}/learn/{enrollment.course_id}"
            )
            if _send(
                db,
                enrollment.user,
                "learning_reminder",
                body,
                context={"progress": enrollment.progress_percent},
            ):
                sent += 1

        logger.info("Eslatmalar yuborildi: %s / %s", sent, len(rows))
        return {"candidates": len(rows), "sent": sent}


@celery_app.task(name="app.worker.tasks.notifications.send_weekly_b2b_reports")
def send_weekly_b2b_reports() -> dict:
    with sync_session() as db:
        orgs = db.scalars(select(Organization).where(Organization.type == "b2b_client")).all()

        sent = 0
        for org in orgs:
            if org.owner_id is None:
                continue
            manager = db.scalar(select(User).where(User.id == org.owner_id))
            if manager is None or not manager.telegram_chat_id:
                continue

            stats = db.execute(
                select(
                    func.count(Enrollment.id),
                    func.coalesce(func.avg(Enrollment.progress_percent), 0),
                ).where(Enrollment.organization_id == org.id)
            ).one()
            completed = db.scalar(
                select(func.count(Enrollment.id)).where(
                    Enrollment.organization_id == org.id,
                    Enrollment.status == EnrollmentStatus.completed,
                )
            )

            body = (
                f"📊 <b>Haftalik hisobot — {org.name}</b>\n\n"
                f"Jami yozilishlar: {int(stats[0] or 0)}\n"
                f"O'rtacha progress: {int(round(float(stats[1] or 0)))}%\n"
                f"Tugatganlar: {int(completed or 0)}\n\n"
                f"Batafsil: {settings.PUBLIC_WEB_URL}/b2b/dashboard"
            )
            if _send(db, manager, "weekly_b2b_report", body, subject="Haftalik hisobot"):
                sent += 1

        return {"organizations": len(orgs), "sent": sent}


@celery_app.task(name="app.worker.tasks.notifications.send_custom_message")
def send_custom_message(user_id: str, body: str, template: str = "custom") -> dict:
    with sync_session() as db:
        user = db.scalar(select(User).where(User.id == uuid.UUID(user_id)))
        return {"sent": _send(db, user, template, body)}
