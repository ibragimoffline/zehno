"""Sertifikat generatsiyasi: PDF (fpdf2) + QR kod + S3'ga saqlash.

`ARCHITECTURE.md` 9-bo'lim: kurs 100% tugallanganda (barcha darslar + quiz
passing_score) `CERTIFICATE_ISSUE` job ishga tushadi, PDF generatsiya qilinadi,
unikal kod + QR biriktiriladi va `/certificates/{code}/verify` orqali istalgan
kishi haqiqiyligini tekshira oladi.
"""

from __future__ import annotations

import io
import logging
import uuid
from datetime import UTC, datetime

import qrcode
from fpdf import FPDF
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import generate_code
from app.integrations.storage.s3 import StorageService
from app.models.catalog import Course
from app.models.certificate import Certificate
from app.models.enums import EnrollmentStatus
from app.models.learning import Enrollment
from app.models.user import User

logger = logging.getLogger(__name__)

# Rang palitrasi (FRONTEND_UX_UI 1.2 bilan mos)
PRIMARY = (37, 99, 235)
SECONDARY = (16, 185, 129)
NEUTRAL_DARK = (15, 23, 42)
NEUTRAL_MID = (100, 116, 139)


class CertificateService:
    """Sinxron servis — Celery worker'dan chaqirish uchun (`sync_session`)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.storage = StorageService()

    def issue(self, enrollment_id: uuid.UUID, *, force: bool = False) -> Certificate:
        enrollment = self.db.scalar(
            select(Enrollment)
            .where(Enrollment.id == enrollment_id)
            .options(
                selectinload(Enrollment.user),
                selectinload(Enrollment.course).selectinload(Course.owner),
                selectinload(Enrollment.certificate),
            )
        )
        if enrollment is None:
            raise NotFoundError("Enrollment topilmadi")

        if enrollment.certificate is not None and not force:
            return enrollment.certificate

        if enrollment.status is not EnrollmentStatus.completed and not force:
            raise ConflictError("Kurs hali tugallanmagan")

        code = self._unique_code()
        verification_url = f"{settings.PUBLIC_WEB_URL.rstrip('/')}/certificates/{code}"

        pdf_bytes = self.render_pdf(
            student_name=enrollment.user.full_name,
            course_title=enrollment.course.title,
            teacher_name=enrollment.course.owner.full_name if enrollment.course.owner else "Zehno",
            code=code,
            verification_url=verification_url,
            issued_at=datetime.now(UTC),
            duration_seconds=enrollment.course.duration_seconds,
        )

        object_key = f"public/certificates/{code}.pdf"
        self.storage.put_object(object_key, pdf_bytes, content_type="application/pdf", public=True)

        certificate = enrollment.certificate or Certificate(enrollment_id=enrollment.id)
        certificate.certificate_code = code
        certificate.pdf_object_key = object_key
        certificate.pdf_url = self.storage.public_url(object_key)
        certificate.verification_url = verification_url
        certificate.snapshot = {
            "student_name": enrollment.user.full_name,
            "student_email": enrollment.user.email,
            "course_title": enrollment.course.title,
            "course_id": str(enrollment.course_id),
            "teacher_name": enrollment.course.owner.full_name if enrollment.course.owner else None,
            "lessons_count": enrollment.course.lessons_count,
            "duration_seconds": enrollment.course.duration_seconds,
            "completed_at": (
                enrollment.completed_at.isoformat() if enrollment.completed_at else None
            ),
        }
        certificate.issued_at = datetime.now(UTC)
        if certificate.id is None:
            self.db.add(certificate)

        self.db.commit()
        logger.info("Sertifikat berildi: %s (%s)", code, enrollment.user.email)
        return certificate

    def _unique_code(self) -> str:
        for _ in range(10):
            code = f"ZH-{generate_code(4)}-{generate_code(4)}"
            exists = self.db.scalar(
                select(Certificate.id).where(Certificate.certificate_code == code)
            )
            if exists is None:
                return code
        raise ConflictError("Unikal sertifikat kodi yaratib bo'lmadi")

    # ------------------------------------------------------------ PDF
    def render_pdf(
        self,
        *,
        student_name: str,
        course_title: str,
        teacher_name: str,
        code: str,
        verification_url: str,
        issued_at: datetime,
        duration_seconds: int = 0,
    ) -> bytes:
        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()

        width, height = pdf.w, pdf.h

        # Ramka
        pdf.set_draw_color(*PRIMARY)
        pdf.set_line_width(2.0)
        pdf.rect(10, 10, width - 20, height - 20)
        pdf.set_draw_color(*SECONDARY)
        pdf.set_line_width(0.4)
        pdf.rect(14, 14, width - 28, height - 28)

        # Brend
        pdf.set_xy(0, 26)
        pdf.set_font("helvetica", "B", 26)
        pdf.set_text_color(*PRIMARY)
        pdf.cell(width, 10, "ZEHNO.UZ", align="C")

        pdf.set_xy(0, 38)
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(*NEUTRAL_MID)
        pdf.cell(width, 6, "Onlayn ta'lim platformasi", align="C")

        # Sarlavha
        pdf.set_xy(0, 54)
        pdf.set_font("helvetica", "B", 30)
        pdf.set_text_color(*NEUTRAL_DARK)
        pdf.cell(width, 12, "SERTIFIKAT", align="C")

        pdf.set_xy(0, 70)
        pdf.set_font("helvetica", "", 12)
        pdf.set_text_color(*NEUTRAL_MID)
        pdf.cell(width, 6, "Ushbu sertifikat quyidagi shaxsga berildi:", align="C")

        # Talaba ismi
        pdf.set_xy(0, 82)
        pdf.set_font("helvetica", "B", 24)
        pdf.set_text_color(*PRIMARY)
        pdf.cell(width, 12, _latinize(student_name), align="C")

        pdf.set_xy(0, 98)
        pdf.set_font("helvetica", "", 12)
        pdf.set_text_color(*NEUTRAL_MID)
        pdf.cell(width, 6, "quyidagi kursni muvaffaqiyatli tamomlagani uchun:", align="C")

        # Kurs nomi
        pdf.set_xy(30, 110)
        pdf.set_font("helvetica", "B", 17)
        pdf.set_text_color(*NEUTRAL_DARK)
        pdf.multi_cell(width - 60, 9, _latinize(course_title), align="C")

        # Ma'lumot qatori
        hours = duration_seconds // 3600
        info_parts = [f"Ustoz: {_latinize(teacher_name)}"]
        if hours:
            info_parts.append(f"Davomiyligi: {hours} soat")
        info_parts.append(f"Sana: {issued_at:%d.%m.%Y}")

        pdf.set_xy(0, height - 62)
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(*NEUTRAL_MID)
        pdf.cell(width, 6, "   |   ".join(info_parts), align="C")

        # QR kod
        qr_image = _qr_png(verification_url)
        qr_path_reader = io.BytesIO(qr_image)
        pdf.image(qr_path_reader, x=width - 52, y=height - 52, w=32, h=32)

        # Sertifikat kodi
        pdf.set_xy(20, height - 40)
        pdf.set_font("courier", "B", 13)
        pdf.set_text_color(*NEUTRAL_DARK)
        pdf.cell(70, 6, code)

        pdf.set_xy(20, height - 32)
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*NEUTRAL_MID)
        pdf.cell(110, 5, "Haqiqiyligini tekshirish:")
        pdf.set_xy(20, height - 27)
        pdf.set_font("helvetica", "", 8)
        pdf.cell(140, 5, verification_url)

        output = pdf.output()
        return bytes(output)


def _qr_png(data: str) -> bytes:
    qr = qrcode.QRCode(version=None, box_size=8, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#0F172A", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


# fpdf2 ning standart shriftlari (Helvetica) faqat latin-1 ni qo'llab-quvvatlaydi.
# O'zbek lotin alifbosi latin-1 ga sig'adi, lekin kirill/maxsus belgilar uchun
# translit qilamiz — aks holda PDF generatsiyasi xato beradi.
_TRANSLIT = {
    "ў": "o'",
    "Ў": "O'",
    "қ": "q",
    "Қ": "Q",
    "ғ": "g'",
    "Ғ": "G'",
    "ҳ": "h",
    "Ҳ": "H",
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "j",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "x",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sh",
    "ъ": "'",
    "ы": "i",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    "А": "A",
    "Б": "B",
    "В": "V",
    "Г": "G",
    "Д": "D",
    "Е": "E",
    "Ё": "Yo",
    "Ж": "J",
    "З": "Z",
    "И": "I",
    "Й": "Y",
    "К": "K",
    "Л": "L",
    "М": "M",
    "Н": "N",
    "О": "O",
    "П": "P",
    "Р": "R",
    "С": "S",
    "Т": "T",
    "У": "U",
    "Ф": "F",
    "Х": "X",
    "Ц": "Ts",
    "Ч": "Ch",
    "Ш": "Sh",
    "Щ": "Sh",
    "Ъ": "'",
    "Ы": "I",
    "Ь": "",
    "Э": "E",
    "Ю": "Yu",
    "Я": "Ya",
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
}


def _latinize(text: str) -> str:
    result = "".join(_TRANSLIT.get(char, char) for char in text or "")
    return result.encode("latin-1", errors="replace").decode("latin-1")


async def get_user_certificates(db, user: User) -> list[Certificate]:
    rows = await db.scalars(
        select(Certificate)
        .join(Enrollment, Certificate.enrollment_id == Enrollment.id)
        .where(Enrollment.user_id == user.id)
        .options(selectinload(Certificate.enrollment).selectinload(Enrollment.course))
        .order_by(Certificate.issued_at.desc())
    )
    return list(rows.all())
