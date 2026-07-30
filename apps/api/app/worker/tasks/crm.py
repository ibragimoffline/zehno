"""CRM sinxronizatsiya task'lari (B2B nazorat).

`ARCHITECTURE.md` 6.2 dagi oqim:
    Talaba darsni ko'radi → "progress_updated" event → Queue → CRM
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import sync_session
from app.integrations.crm.base import CrmCompany, CrmContact, CrmProgressUpdate
from app.integrations.factory import get_crm_provider
from app.models.certificate import Certificate
from app.models.crm import CrmSyncLog
from app.models.enums import CrmSyncStatus
from app.models.learning import Enrollment
from app.models.organization import Organization
from app.models.user import User
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    """Sinxron Celery task ichida async adapterni chaqirish."""
    return asyncio.run(coro)


@celery_app.task(
    name="app.worker.tasks.crm.sync_enrollment_to_crm",
    bind=True,
    max_retries=5,
    default_retry_delay=60,
)
def sync_enrollment_to_crm(self, enrollment_id: str) -> dict:
    """Yangi enrollment → CRM'da Contact yaratish/yangilash."""
    with sync_session() as db:
        enrollment = db.scalar(
            select(Enrollment)
            .where(Enrollment.id == uuid.UUID(enrollment_id))
            .options(
                selectinload(Enrollment.user),
                selectinload(Enrollment.course),
                selectinload(Enrollment.organization),
            )
        )
        if enrollment is None:
            return {"skipped": "enrollment topilmadi"}

        org = enrollment.organization
        if org is None or not org.crm_sync_enabled:
            return {"skipped": "CRM sinxronizatsiyasi yoqilmagan"}

        provider = get_crm_provider(org.crm_provider)
        log = CrmSyncLog(
            organization_id=org.id,
            user_id=enrollment.user_id,
            provider=provider.provider_name,
            event_type="enrollment_created",
            payload={
                "course": enrollment.course.title,
                "email": enrollment.user.email,
            },
        )
        db.add(log)
        db.flush()

        try:
            company_id = org.crm_company_id
            if not company_id:
                company_id = _run(
                    provider.upsert_company(
                        CrmCompany(
                            name=org.name,
                            external_id=org.crm_company_id,
                            email=org.contact_email,
                            phone=org.contact_phone,
                            website=org.website,
                        )
                    )
                )
                org.crm_company_id = company_id

            contact_id = _run(
                provider.upsert_contact(
                    CrmContact(
                        full_name=enrollment.user.full_name,
                        email=enrollment.user.email,
                        phone=enrollment.user.phone,
                        external_id=None,
                        company_external_id=company_id,
                        custom_fields={"COMMENTS": f"Zehno.uz — {enrollment.course.title}"},
                    )
                )
            )

            log.status = CrmSyncStatus.success
            log.external_id = contact_id
            log.synced_at = datetime.now(UTC)
            log.attempts = (log.attempts or 0) + 1
            db.commit()
            return {"contact_id": contact_id, "company_id": company_id}

        except Exception as exc:
            log.status = CrmSyncStatus.failed
            log.error_message = str(exc)[:1000]
            log.attempts = (log.attempts or 0) + 1
            db.commit()
            logger.warning("CRM enrollment sync xato: %s", exc)
            raise self.retry(exc=exc) from exc


@celery_app.task(
    name="app.worker.tasks.crm.sync_progress_to_crm",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def sync_progress_to_crm(self, enrollment_id: str) -> dict:
    """Progress o'zgarganda CRM'ga yozadi (timeline comment / custom field)."""
    with sync_session() as db:
        enrollment = db.scalar(
            select(Enrollment)
            .where(Enrollment.id == uuid.UUID(enrollment_id))
            .options(
                selectinload(Enrollment.user),
                selectinload(Enrollment.course),
                selectinload(Enrollment.organization),
                selectinload(Enrollment.certificate),
            )
        )
        if enrollment is None:
            return {"skipped": "enrollment topilmadi"}

        org = enrollment.organization
        if org is None or not org.crm_sync_enabled:
            return {"skipped": "CRM sinxronizatsiyasi yoqilmagan"}

        # Faqat muhim bosqichlarda yuboramiz — CRM'ni spam qilmaslik uchun
        milestones = {25, 50, 75, 100}
        if enrollment.progress_percent not in milestones:
            return {"skipped": f"progress {enrollment.progress_percent}% — milestone emas"}

        provider = get_crm_provider(org.crm_provider)
        last_contact = db.scalar(
            select(CrmSyncLog)
            .where(
                CrmSyncLog.organization_id == org.id,
                CrmSyncLog.user_id == enrollment.user_id,
                CrmSyncLog.status == CrmSyncStatus.success,
                CrmSyncLog.external_id.isnot(None),
            )
            .order_by(CrmSyncLog.created_at.desc())
        )
        if last_contact is None or not last_contact.external_id:
            # Avval kontaktni yaratamiz
            sync_enrollment_to_crm.delay(enrollment_id)
            return {"deferred": "kontakt hali yaratilmagan"}

        log = CrmSyncLog(
            organization_id=org.id,
            user_id=enrollment.user_id,
            provider=provider.provider_name,
            event_type="progress_updated",
            payload={
                "progress": enrollment.progress_percent,
                "course": enrollment.course.title,
            },
            external_id=last_contact.external_id,
        )
        db.add(log)
        db.flush()

        try:
            _run(
                provider.push_progress(
                    CrmProgressUpdate(
                        contact_external_id=last_contact.external_id,
                        course_title=enrollment.course.title,
                        progress_percent=enrollment.progress_percent,
                        completed=enrollment.progress_percent >= 100,
                        certificate_code=(
                            enrollment.certificate.certificate_code
                            if enrollment.certificate
                            else None
                        ),
                    )
                )
            )
            log.status = CrmSyncStatus.success
            log.synced_at = datetime.now(UTC)
            log.attempts = (log.attempts or 0) + 1
            db.commit()
            return {"ok": True, "progress": enrollment.progress_percent}
        except Exception as exc:
            log.status = CrmSyncStatus.failed
            log.error_message = str(exc)[:1000]
            log.attempts = (log.attempts or 0) + 1
            db.commit()
            raise self.retry(exc=exc) from exc


@celery_app.task(name="app.worker.tasks.crm.sync_organization_to_crm")
def sync_organization_to_crm(organization_id: str) -> dict:
    """Qo'lda "sinxronlash" tugmasi — tashkilot va barcha a'zolarini CRM'ga yuboradi."""
    with sync_session() as db:
        org = db.scalar(select(Organization).where(Organization.id == uuid.UUID(organization_id)))
        if org is None:
            return {"error": "tashkilot topilmadi"}
        if not org.crm_sync_enabled:
            return {"skipped": "CRM sinxronizatsiyasi yoqilmagan"}

        provider = get_crm_provider(org.crm_provider)
        try:
            company_id = _run(
                provider.upsert_company(
                    CrmCompany(
                        name=org.name,
                        external_id=org.crm_company_id,
                        email=org.contact_email,
                        phone=org.contact_phone,
                        website=org.website,
                    )
                )
            )
            org.crm_company_id = company_id
            org.crm_provider = provider.provider_name
            db.commit()
        except Exception as exc:
            db.add(
                CrmSyncLog(
                    organization_id=org.id,
                    provider=provider.provider_name,
                    event_type="company_sync",
                    status=CrmSyncStatus.failed,
                    error_message=str(exc)[:1000],
                    attempts=1,
                )
            )
            db.commit()
            return {"error": str(exc)}

        members = db.scalars(select(User).where(User.organization_id == org.id)).all()
        synced = 0
        for member in members:
            try:
                contact_id = _run(
                    provider.upsert_contact(
                        CrmContact(
                            full_name=member.full_name,
                            email=member.email,
                            phone=member.phone,
                            company_external_id=company_id,
                        )
                    )
                )
                db.add(
                    CrmSyncLog(
                        organization_id=org.id,
                        user_id=member.id,
                        provider=provider.provider_name,
                        event_type="contact_sync",
                        status=CrmSyncStatus.success,
                        external_id=contact_id,
                        synced_at=datetime.now(UTC),
                        attempts=1,
                    )
                )
                synced += 1
            except Exception as exc:
                db.add(
                    CrmSyncLog(
                        organization_id=org.id,
                        user_id=member.id,
                        provider=provider.provider_name,
                        event_type="contact_sync",
                        status=CrmSyncStatus.failed,
                        error_message=str(exc)[:1000],
                        attempts=1,
                    )
                )
        db.commit()
        logger.info("CRM org sync: %s (%s kontakt)", org.slug, synced)
        return {"company_id": company_id, "contacts_synced": synced, "members": len(members)}


@celery_app.task(name="app.worker.tasks.crm.retry_failed_syncs")
def retry_failed_syncs(limit: int = 50) -> dict:
    """Beat: muvaffaqiyatsiz sinxronizatsiyalarni qayta urinish."""
    with sync_session() as db:
        rows = db.scalars(
            select(CrmSyncLog)
            .where(CrmSyncLog.status == CrmSyncStatus.failed, CrmSyncLog.attempts < 5)
            .order_by(CrmSyncLog.created_at.asc())
            .limit(limit)
        ).all()

        requeued = 0
        for row in rows:
            if row.event_type == "enrollment_created" and row.user_id:
                enrollment = db.scalar(
                    select(Enrollment).where(
                        Enrollment.user_id == row.user_id,
                        Enrollment.organization_id == row.organization_id,
                    )
                )
                if enrollment:
                    sync_enrollment_to_crm.delay(str(enrollment.id))
                    requeued += 1
            elif row.event_type == "company_sync" and row.organization_id:
                sync_organization_to_crm.delay(str(row.organization_id))
                requeued += 1

        return {"checked": len(rows), "requeued": requeued}


@celery_app.task(name="app.worker.tasks.crm.sync_certificate_to_crm")
def sync_certificate_to_crm(certificate_id: str) -> dict:
    """Sertifikat berilganda CRM'ga yozish."""
    with sync_session() as db:
        certificate = db.scalar(
            select(Certificate)
            .where(Certificate.id == uuid.UUID(certificate_id))
            .options(selectinload(Certificate.enrollment).selectinload(Enrollment.course))
        )
        if certificate is None or certificate.enrollment is None:
            return {"skipped": "sertifikat topilmadi"}
        sync_progress_to_crm.delay(str(certificate.enrollment_id))
        return {"queued": True}
