from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JSONType, UUIDType
from app.models.enums import EnrollmentSource, EnrollmentStatus

if TYPE_CHECKING:
    from app.models.catalog import Course, Lesson
    from app.models.certificate import Certificate
    from app.models.commerce import Order
    from app.models.organization import Organization
    from app.models.user import User


class Enrollment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),
        Index("ix_enrollments_course_status", "course_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("orders.id", ondelete="SET NULL")
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )

    source: Mapped[EnrollmentSource] = mapped_column(
        Enum(EnrollmentSource, native_enum=False, length=20, validate_strings=True),
        default=EnrollmentSource.individual,
        nullable=False,
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, native_enum=False, length=20, validate_strings=True),
        default=EnrollmentStatus.active,
        nullable=False,
        index=True,
    )

    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_lessons: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("lessons.id", ondelete="SET NULL")
    )

    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="enrollments")
    course: Mapped[Course] = relationship(back_populates="enrollments")
    order: Mapped[Order | None] = relationship(back_populates="enrollments")
    organization: Mapped[Organization | None] = relationship()
    lesson_progress: Mapped[list[LessonProgress]] = relationship(
        back_populates="enrollment", cascade="all, delete-orphan"
    )
    certificate: Mapped[Certificate | None] = relationship(
        back_populates="enrollment", cascade="all, delete-orphan", uselist=False
    )

    @property
    def is_completed(self) -> bool:
        return self.status is EnrollmentStatus.completed


class LessonProgress(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "lesson_id", name="uq_progress_enrollment_lesson"),
    )

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    watch_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_position_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    enrollment: Mapped[Enrollment] = relationship(back_populates="lesson_progress")
    lesson: Mapped[Lesson] = relationship()


class Quiz(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quizzes"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("lessons.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(200))
    questions: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    passing_score: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    lesson: Mapped[Lesson] = relationship(back_populates="quiz")
    attempts: Mapped[list[QuizAttempt]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )


class QuizAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (Index("ix_quiz_attempts_quiz_user", "quiz_id", "user_id"),)

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    enrollment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("enrollments.id", ondelete="CASCADE")
    )
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    answers: Mapped[dict | None] = mapped_column(JSONType)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    quiz: Mapped[Quiz] = relationship(back_populates="attempts")
    user: Mapped[User] = relationship()
