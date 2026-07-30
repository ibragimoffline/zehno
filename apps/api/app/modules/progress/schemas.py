"""Progress va quiz sxemalari."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import EnrollmentSource, EnrollmentStatus
from app.modules.courses.schemas import CourseCard, ModuleDetail
from app.schemas.common import ORMModel


class EnrollmentView(ORMModel):
    id: uuid.UUID
    course: CourseCard
    status: EnrollmentStatus
    source: EnrollmentSource
    progress_percent: int
    completed_lessons: int
    last_lesson_id: uuid.UUID | None = None
    enrolled_at: datetime
    completed_at: datetime | None = None
    has_certificate: bool = False


class LearnCourseView(BaseModel):
    """Course Player sahifasi uchun to'liq ma'lumot (FRONTEND_UX_UI 5)."""

    enrollment_id: uuid.UUID
    course: CourseCard
    progress_percent: int
    completed_lessons: int
    total_lessons: int
    modules: list[ModuleDetail]
    current_lesson_id: uuid.UUID | None = None
    sequential_progress: bool = False
    certificate_code: str | None = None


class ProgressUpdateRequest(BaseModel):
    lesson_id: uuid.UUID
    watch_seconds: int | None = Field(default=None, ge=0)
    position_seconds: int | None = Field(default=None, ge=0)
    completed: bool | None = None


class ProgressUpdateResponse(BaseModel):
    lesson_id: uuid.UUID
    completed: bool
    watch_seconds: int
    last_position_seconds: int
    course_progress_percent: int
    course_completed: bool
    next_lesson_id: uuid.UUID | None = None
    certificate_issued: bool = False


# ------------------------------------------------------------------ quiz
class QuizOption(BaseModel):
    id: str
    text: str


class QuizQuestionPublic(BaseModel):
    """Talabaga yuboriladigan savol — `correct` maydoni YO'Q."""

    id: str
    text: str
    type: str = "single"
    options: list[QuizOption] = []
    points: int = 1


class QuizPublic(BaseModel):
    id: uuid.UUID
    lesson_id: uuid.UUID
    title: str | None = None
    passing_score: int
    max_attempts: int
    time_limit_minutes: int | None = None
    questions: list[QuizQuestionPublic]
    attempts_used: int = 0
    best_score: int | None = None
    passed: bool = False


class QuizQuestionUpsert(BaseModel):
    id: str | None = None
    text: str = Field(min_length=1, max_length=1000)
    type: str = Field(default="single", pattern="^(single|multiple|boolean)$")
    options: list[QuizOption] = Field(min_length=2)
    correct: list[str] = Field(min_length=1)
    points: int = Field(default=1, ge=1, le=100)


class QuizUpsert(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    passing_score: int = Field(default=60, ge=1, le=100)
    max_attempts: int = Field(default=0, ge=0, le=100)
    time_limit_minutes: int | None = Field(default=None, ge=1, le=600)
    shuffle_questions: bool = False
    questions: list[QuizQuestionUpsert] = Field(min_length=1)


class QuizSubmitRequest(BaseModel):
    answers: dict[str, list[str]] = Field(
        description='Savol id → tanlangan variant id\'lari, masalan {"q1": ["a"]}'
    )


class QuizSubmitResponse(BaseModel):
    score: int
    passed: bool
    passing_score: int
    correct_count: int
    total_questions: int
    attempt_number: int
    details: list[dict] = []
    course_progress_percent: int = 0
    certificate_issued: bool = False
