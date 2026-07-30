"""Kurs katalogi va CMS sxemalari."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import (
    CourseLanguage,
    CourseLevel,
    CourseStatus,
    EnrollmentStatus,
    LessonContentType,
    VideoAssetStatus,
)
from app.schemas.common import ORMModel


# ----------------------------------------------------------------- kategoriya
class CategoryPublic(ORMModel):
    id: uuid.UUID
    name: str
    slug: str
    icon: str | None = None
    description: str | None = None
    order_index: int = 0
    courses_count: int = 0


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    icon: str | None = Field(default=None, max_length=64)
    description: str | None = None
    order_index: int = 0
    parent_id: uuid.UUID | None = None


# ----------------------------------------------------------------- ustoz
class CourseOwner(ORMModel):
    id: uuid.UUID
    full_name: str
    avatar_url: str | None = None
    bio: str | None = None


# ----------------------------------------------------------------- kurs
class CourseBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    description: str | None = None
    category_id: uuid.UUID | None = None
    level: CourseLevel = CourseLevel.beginner
    language: CourseLanguage = CourseLanguage.uz
    price: Decimal = Field(default=Decimal("0"), ge=0, le=Decimal("999999999"))
    discount_price: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="UZS", min_length=3, max_length=3)
    cover_url: str | None = Field(default=None, max_length=512)
    promo_video_url: str | None = Field(default=None, max_length=512)
    what_you_learn: list[str] | None = None
    requirements: list[str] | None = None
    target_audience: list[str] | None = None
    has_certificate: bool = True
    sequential_progress: bool = False
    completion_threshold: int = Field(default=100, ge=1, le=100)


class CourseCreate(CourseBase):
    @field_validator("discount_price")
    @classmethod
    def _discount_lower(cls, value: Decimal | None, info) -> Decimal | None:
        price = info.data.get("price")
        if value is not None and price is not None and value >= price:
            raise ValueError("Chegirma narxi asosiy narxdan kichik bo'lishi kerak")
        return value


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    description: str | None = None
    category_id: uuid.UUID | None = None
    level: CourseLevel | None = None
    language: CourseLanguage | None = None
    price: Decimal | None = Field(default=None, ge=0)
    discount_price: Decimal | None = Field(default=None, ge=0)
    cover_url: str | None = Field(default=None, max_length=512)
    promo_video_url: str | None = Field(default=None, max_length=512)
    what_you_learn: list[str] | None = None
    requirements: list[str] | None = None
    target_audience: list[str] | None = None
    has_certificate: bool | None = None
    sequential_progress: bool | None = None
    completion_threshold: int | None = Field(default=None, ge=1, le=100)


class CourseCard(ORMModel):
    """Katalog kartochkasi (FRONTEND_UX_UI 4.1)."""

    id: uuid.UUID
    title: str
    slug: str
    subtitle: str | None = None
    cover_url: str | None = None
    price: Decimal
    discount_price: Decimal | None = None
    currency: str
    level: CourseLevel
    language: CourseLanguage
    rating_avg: float = 0
    rating_count: int = 0
    students_count: int = 0
    lessons_count: int = 0
    duration_seconds: int = 0
    is_bestseller: bool = False
    is_featured: bool = False
    owner: CourseOwner | None = None
    category: CategoryPublic | None = None
    is_enrolled: bool = False


# ----------------------------------------------------------------- dars
class LessonBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    content_type: LessonContentType = LessonContentType.video
    duration_seconds: int = Field(default=0, ge=0)
    text_content: str | None = None
    attachments: list[dict] | None = None
    is_preview: bool = False
    is_published: bool = True


class LessonCreate(LessonBase):
    order_index: int | None = Field(default=None, ge=0)


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    content_type: LessonContentType | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    text_content: str | None = None
    attachments: list[dict] | None = None
    is_preview: bool | None = None
    is_published: bool | None = None
    order_index: int | None = Field(default=None, ge=0)


class VideoAssetPublic(ORMModel):
    id: uuid.UUID
    provider: str
    status: VideoAssetStatus
    duration_seconds: int = 0
    thumbnail_url: str | None = None


class LessonPublic(ORMModel):
    """Katalogda ko'rinadigan dars (video havolasi YO'Q)."""

    id: uuid.UUID
    title: str
    description: str | None = None
    content_type: LessonContentType
    order_index: int
    duration_seconds: int
    is_preview: bool
    has_video: bool = False
    has_quiz: bool = False


class LessonDetail(LessonPublic):
    """Sotib olgan talaba uchun to'liq dars."""

    text_content: str | None = None
    attachments: list[dict] | None = None
    video: VideoAssetPublic | None = None
    completed: bool = False
    watch_seconds: int = 0
    last_position_seconds: int = 0
    is_locked: bool = False


# ----------------------------------------------------------------- modul
class ModuleBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ModuleCreate(ModuleBase):
    order_index: int | None = Field(default=None, ge=0)


class ModuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    order_index: int | None = Field(default=None, ge=0)


class ModulePublic(ORMModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    order_index: int
    lessons: list[LessonPublic] = []
    duration_seconds: int = 0


class ModuleDetail(ORMModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    order_index: int
    lessons: list[LessonDetail] = []


class ReorderItem(BaseModel):
    id: uuid.UUID
    order_index: int


class ReorderRequest(BaseModel):
    """Drag & drop natijasi (FRONTEND_UX_UI 6.3)."""

    items: list[ReorderItem] = Field(min_length=1)


# ----------------------------------------------------------------- to'liq kurs
class CourseDetail(CourseCard):
    description: str | None = None
    status: CourseStatus
    what_you_learn: list[str] | None = None
    requirements: list[str] | None = None
    target_audience: list[str] | None = None
    has_certificate: bool = True
    sequential_progress: bool = False
    completion_threshold: int = 100
    modules: list[ModulePublic] = []
    organization_id: uuid.UUID | None = None
    published_at: datetime | None = None
    created_at: datetime


class CourseAdminSummary(CourseCard):
    """Teacher/admin ro'yxatlari uchun — `modules` YO'Q.

    `modules` maydonini qo'shish uchun modullar va darslar eager-load qilingan
    bo'lishi shart (async SQLAlchemy lazy-load qila olmaydi), shuning uchun
    ro'yxat va CRUD javoblarida faqat kurs darajasidagi maydonlar qaytadi.
    """

    description: str | None = None
    status: CourseStatus
    what_you_learn: list[str] | None = None
    requirements: list[str] | None = None
    target_audience: list[str] | None = None
    has_certificate: bool = True
    sequential_progress: bool = False
    completion_threshold: int = 100
    organization_id: uuid.UUID | None = None
    owner_id: uuid.UUID
    published_at: datetime | None = None
    submitted_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class CourseAdminDetail(CourseAdminSummary):
    """Kursni tahrirlash sahifasi uchun — modul/dars daraxti bilan."""

    modules: list[ModulePublic] = []


# ----------------------------------------------------------------- moderatsiya
class ModerationDecision(BaseModel):
    comment: str | None = Field(default=None, max_length=1000)


class ModerationRejection(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class ModerationLogView(ORMModel):
    id: uuid.UUID
    action: str
    from_status: str | None = None
    to_status: str | None = None
    comment: str | None = None
    actor_id: uuid.UUID | None = None
    created_at: datetime


# ----------------------------------------------------------------- sharh
class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewPublic(ORMModel):
    id: uuid.UUID
    rating: int
    comment: str | None = None
    created_at: datetime
    user: CourseOwner | None = None


# ----------------------------------------------------------------- talabalar
class TeacherStudentRow(ORMModel):
    """Ustoz kabinetidagi "Talabalar" jadvali qatori."""

    id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    status: EnrollmentStatus
    progress_percent: int
    completed_lessons: int
    enrolled_at: datetime
    completed_at: datetime | None = None
    user_name: str | None = None
    user_email: str | None = None
    course_title: str | None = None
