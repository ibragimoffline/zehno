"""Sertifikat generatsiyasi task'lari."""

from __future__ import annotations

import logging
import uuid

from app.db.session import sync_session
from app.modules.certificates.service import CertificateService
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.worker.tasks.certificates.issue_certificate",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def issue_certificate(self, enrollment_id: str) -> dict:
    """`CERTIFICATE_ISSUE` — kurs 100% tugallanganda ishga tushadi."""
    try:
        with sync_session() as db:
            certificate = CertificateService(db).issue(uuid.UUID(enrollment_id))
            result = {
                "certificate_code": certificate.certificate_code,
                "pdf_url": certificate.pdf_url,
                "enrollment_id": enrollment_id,
            }
    except Exception as exc:
        logger.exception("Sertifikat generatsiyasi xato: %s", enrollment_id)
        raise self.retry(exc=exc) from exc

    # Telegram orqali xabar beramiz
    from app.worker.tasks.notifications import notify_certificate_ready

    notify_certificate_ready.delay(enrollment_id, result["certificate_code"])
    logger.info("Sertifikat tayyor: %s", result["certificate_code"])
    return result


@celery_app.task(name="app.worker.tasks.certificates.regenerate_certificate")
def regenerate_certificate(enrollment_id: str) -> dict:
    """Admin uchun: sertifikatni qayta generatsiya qilish (shablon o'zgarganda)."""
    with sync_session() as db:
        certificate = CertificateService(db).issue(uuid.UUID(enrollment_id), force=True)
        return {"certificate_code": certificate.certificate_code, "pdf_url": certificate.pdf_url}
