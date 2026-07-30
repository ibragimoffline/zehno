"""Kurs katalogi modellari: kategoriya, kurs, modul, dars, video asset, sharh."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JSONType, UUIDType
from app.models.enums import (
    CourseLanguage,
    CourseLevel,
    CourseStatus,
    LessonContentType,
    ModerationAction,
    ReviewStatus,
    VideoAssetStatus,
)

if TYPE_CHECKING:
    from app.models.learning import Enrollment, Quiz
    from app.models.organization import Organization
    from app.models.user import User


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("categories.id", ondelete="SET NULL")
    )

    courses: Mapped[list[Course]] = relationship(back_populates="category")
    parent: Mapped[Category | None] = relationship(
        back_populates="children", remote_side=lambda: [Category.id]
    )
    children: Mapped[list[Category]] = relationship(back_populates="parent")


class Course(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (
        Index("ix_courses_status_published", "status", "published_at"),
        Index("ix_courses_owner_status", "owner_id", "status"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(512))
    promo_video_url: Mapped[str | None] = mapped_column(String(512))

    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="UZS", nullable=False)

    level: Mapped[CourseLevel] = mapped_column(
        Enum(CourseLevel, native_enum=False, length=20, validate_strings=True),
        default=CourseLevel.beginner,
        nullable=False,
    )
    language: Mapped[CourseLanguage] = mapped_column(
        Enum(CourseLanguage, native_enum=False, length=5, validate_strings=True),
        default=CourseLanguage.uz,
        nullable=False,
    )
    status: Mapped[CourseStatus] = mapped_column(
        Enum(CourseStatus, native_enum=False, length=20, validate_strings=True),
        default=CourseStatus.draft,
        nullable=False,
        index=True,
    )

    # Kursning "Bu kursda nima bor" bloklari (FRONTEND_UX_UI 4.2)
    what_you_learn: Mapped[list | None] = mapped_column(JSONType)
    requirements: Mapped[list | None] = mapped_column(JSONType)
    target_audience: Mapped[list | None] = mapped_column(JSONType)

    # Sertifikat / ketma-ketlik qoidalari
    has_certificate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sequential_progress: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completion_threshold: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # Denormalizatsiya qilingan ko'rsatkichlar (katalogda tez ko'rsatish uchun)
    lessons_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating_avg: Mapped[float] = mapped_column(Numeric(3, 2), default=0, nullable=False)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_bestseller: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    owner: Mapped[User] = relationship(back_populates="owned_courses", foreign_keys=[owner_id])
    organization: Mapped[Organization | None] = relationship(back_populates="courses")
    category: Mapped[Category | None] = relationship(back_populates="courses")
    modules: Mapped[list[CourseModule]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseModule.order_index",
    )
    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="course")
    reviews: Mapped[list[CourseReview]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    moderation_logs: Mapped[list[ModerationLog]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )

    @property
    def effective_price(self) -> Decimal:
        return self.discount_price if self.discount_price is not None else self.price

    @property
    def is_free(self) -> bool:
        return self.effective_price <= 0


class CourseModule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Kurs bo'limi (modul). `module` Python'da band so'z bo'lgani uchun `CourseModule`."""

    __tablename__ = "modules"
    __table_args__ = (Index("ix_modules_course_order", "course_id", "order_index"),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    course: Mapped[Course] = relationship(back_populates="modules")
    lessons: Mapped[list[Lesson]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index",
    )


class Lesson(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lessons"
    __table_args__ = (Index("ix_lessons_module_order", "module_id", "order_index"),)

    module_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[LessonContentType] = mapped_column(
        Enum(LessonContentType, native_enum=False, length=10, validate_strings=True),
        default=LessonContentType.video,
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # `text` turi uchun kontent, `pdf` uchun fayl havolasi
    text_content: Mapped[str | None] = mapped_column(Text)
    attachments: Mapped[list | None] = mapped_column(JSONType)

    is_preview: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    module: Mapped[CourseModule] = relationship(back_populates="lessons")
    video_asset: Mapped[VideoAsset | None] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", uselist=False
    )
    quiz: Mapped[Quiz | None] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", uselist=False
    )


class VideoAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "video_assets"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("lessons.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    external_video_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[VideoAssetStatus] = mapped_column(
        Enum(VideoAssetStatus, native_enum=False, length=20, validate_strings=True),
        default=VideoAssetStatus.processing,
        nullable=False,
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    provider_meta: Mapped[dict | None] = mapped_column(JSONType)
    error_message: Mapped[str | None] = mapped_column(Text)

    lesson: Mapped[Lesson] = relationship(back_populates="video_asset")


class CourseReview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Sharh va reyting (ADDITIONAL_FEATURES 8.1 — eng yuqori ROI)."""

    __tablename__ = "course_reviews"
    __table_args__ = (UniqueConstraint("course_id", "user_id", name="uq_review_course_user"),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, native_enum=False, length=20, validate_strings=True),
        default=ReviewStatus.approved,
        nullable=False,
        index=True,
    )

    course: Mapped[Course] = relationship(back_populates="reviews")
    user: Mapped[User] = relationship()


class ModerationLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Kim, qachon, qaysi kursni tasdiqlagani/rad etgani (FRONTEND_UX_UI 7.1)."""

    __tablename__ = "moderation_logs"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[ModerationAction] = mapped_column(
        Enum(ModerationAction, native_enum=False, length=20, validate_strings=True),
        nullable=False,
    )
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str | None] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(Text)

    course: Mapped[Course] = relationship(back_populates="moderation_logs")
    actor: Mapped[User | None] = relationship()
