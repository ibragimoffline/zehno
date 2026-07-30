from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import sync_session
from app.models.catalog import Course
from app.models.certificate import Certificate
from app.models.learning import Enrollment
from app.modules.certificates.service import CertificateService, get_user_certificates
from app.schemas.common import ORMModel

router = APIRouter(tags=["Certificates"])


class CertificateView(ORMModel):
    id: uuid.UUID
    certificate_code: str
    pdf_url: str | None = None
    verification_url: str | None = None
    issued_at: datetime
    course_title: str | None = None
    course_id: uuid.UUID | None = None


class CertificateVerification(BaseModel):
    valid: bool
    certificate_code: str
    student_name: str | None = None
    course_title: str | None = None
    teacher_name: str | None = None
    issued_at: datetime | None = None
    pdf_url: str | None = None
    message: str


@router.get(
    "/certificates/me", response_model=list[CertificateView], summary="Mening sertifikatlarim"
)
async def my_certificates(user: CurrentUser, db: DbSession) -> list[CertificateView]:
    certificates = await get_user_certificates(db, user)
    result = []
    for certificate in certificates:
        view = CertificateView.model_validate(certificate)
        course = certificate.enrollment.course if certificate.enrollment else None
        view.course_title = course.title if course else None
        view.course_id = course.id if course else None
        result.append(view)
    return result


@router.post(
    "/enrollments/{enrollment_id}/certificate",
    response_model=CertificateView,
    summary="Sertifikatni olish (kurs tugallangan bo'lsa)",
)
async def issue_certificate(
    enrollment_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> CertificateView:
    enrollment = await db.scalar(
        select(Enrollment)
        .where(Enrollment.id == enrollment_id, Enrollment.user_id == user.id)
        .options(selectinload(Enrollment.certificate), selectinload(Enrollment.course))
    )
    if enrollment is None:
        raise NotFoundError("Enrollment topilmadi")

    if enrollment.certificate is not None:
        view = CertificateView.model_validate(enrollment.certificate)
        view.course_title = enrollment.course.title
        view.course_id = enrollment.course_id
        return view

    if not enrollment.course.has_certificate:
        raise ConflictError("Bu kursda sertifikat berilmaydi")

    def _generate() -> dict:
        with sync_session() as session:
            certificate = CertificateService(session).issue(enrollment_id)
            return {
                "id": certificate.id,
                "certificate_code": certificate.certificate_code,
                "pdf_url": certificate.pdf_url,
                "verification_url": certificate.verification_url,
                "issued_at": certificate.issued_at,
            }

    data = await asyncio.to_thread(_generate)
    view = CertificateView(**data)
    view.course_title = enrollment.course.title
    view.course_id = enrollment.course_id
    return view


@router.get(
    "/certificates/{code}/verify",
    response_model=CertificateVerification,
    summary="Sertifikat haqiqiyligini tekshirish (ochiq)",
)
async def verify_certificate(code: str, db: DbSession) -> CertificateVerification:
    certificate = await db.scalar(
        select(Certificate)
        .where(Certificate.certificate_code == code.upper().strip())
        .options(
            selectinload(Certificate.enrollment).selectinload(Enrollment.user),
            selectinload(Certificate.enrollment)
            .selectinload(Enrollment.course)
            .selectinload(Course.owner),
        )
    )
    if certificate is None:
        return CertificateVerification(
            valid=False,
            certificate_code=code,
            message="Bunday kod bilan sertifikat topilmadi",
        )

    if certificate.revoked_at is not None:
        return CertificateVerification(
            valid=False,
            certificate_code=certificate.certificate_code,
            issued_at=certificate.issued_at,
            message="Sertifikat bekor qilingan",
        )

    snapshot = certificate.snapshot or {}
    enrollment = certificate.enrollment
    return CertificateVerification(
        valid=True,
        certificate_code=certificate.certificate_code,
        student_name=snapshot.get("student_name")
        or (enrollment.user.full_name if enrollment and enrollment.user else None),
        course_title=snapshot.get("course_title")
        or (enrollment.course.title if enrollment and enrollment.course else None),
        teacher_name=snapshot.get("teacher_name"),
        issued_at=certificate.issued_at,
        pdf_url=certificate.pdf_url,
        message="Sertifikat haqiqiy",
    )
