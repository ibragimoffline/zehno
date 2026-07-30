from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.models.catalog import Course, CourseModule, Lesson
from app.models.certificate import Certificate
from app.models.enums import EnrollmentStatus
from app.models.learning import Enrollment, LessonProgress, Quiz, QuizAttempt
from app.models.user import User

logger = logging.getLogger(__name__)


class ProgressService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_enrollments(
        self, user: User, status_filter: EnrollmentStatus | None = None
    ) -> list[Enrollment]:
        stmt = (
            select(Enrollment)
            .where(Enrollment.user_id == user.id)
            .options(
                selectinload(Enrollment.course).selectinload(Course.owner),
                selectinload(Enrollment.course).selectinload(Course.category),
                selectinload(Enrollment.certificate),
            )
            .order_by(Enrollment.enrolled_at.desc())
        )
        if status_filter is not None:
            stmt = stmt.where(Enrollment.status == status_filter)
        return list((await self.db.scalars(stmt)).all())

    async def get_enrollment(self, user: User, course_id: uuid.UUID) -> Enrollment:
        enrollment = await self.db.scalar(
            select(Enrollment)
            .where(Enrollment.user_id == user.id, Enrollment.course_id == course_id)
            .options(selectinload(Enrollment.certificate))
        )
        if enrollment is None:
            raise PermissionDeniedError("Bu kursga yozilmagansiz")
        return enrollment

    async def load_course_for_learning(self, course_id: uuid.UUID) -> Course:
        course = await self.db.scalar(
            select(Course)
            .where(Course.id == course_id)
            .options(
                selectinload(Course.owner),
                selectinload(Course.category),
                selectinload(Course.modules)
                .selectinload(CourseModule.lessons)
                .selectinload(Lesson.video_asset),
                selectinload(Course.modules)
                .selectinload(CourseModule.lessons)
                .selectinload(Lesson.quiz),
            )
        )
        if course is None:
            raise NotFoundError("Kurs topilmadi")
        return course

    async def progress_rows(self, enrollment_id: uuid.UUID) -> list[LessonProgress]:
        rows = await self.db.scalars(
            select(LessonProgress).where(LessonProgress.enrollment_id == enrollment_id)
        )
        return list(rows.all())

    async def update_progress(
        self,
        user: User,
        enrollment_id: uuid.UUID,
        lesson_id: uuid.UUID,
        *,
        watch_seconds: int | None = None,
        position_seconds: int | None = None,
        completed: bool | None = None,
    ) -> tuple[LessonProgress, Enrollment, uuid.UUID | None, bool]:
        enrollment = await self.db.scalar(
            select(Enrollment).where(Enrollment.id == enrollment_id, Enrollment.user_id == user.id)
        )
        if enrollment is None:
            raise NotFoundError("Enrollment topilmadi")

        lesson = await self.db.scalar(
            select(Lesson).where(Lesson.id == lesson_id).options(selectinload(Lesson.module))
        )
        if lesson is None:
            raise NotFoundError("Dars topilmadi")
        if lesson.module.course_id != enrollment.course_id:
            raise ValidationError("Bu dars kursga tegishli emas")

        course = await self.load_course_for_learning(enrollment.course_id)

        if course.sequential_progress and completed:
            await self._assert_previous_completed(enrollment, course, lesson)

        progress = await self.db.scalar(
            select(LessonProgress).where(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.lesson_id == lesson.id,
            )
        )
        if progress is None:
            progress = LessonProgress(
                enrollment_id=enrollment.id,
                lesson_id=lesson.id,
                completed=False,
                watch_seconds=0,
                last_position_seconds=0,
            )
            self.db.add(progress)

        if watch_seconds is not None:
            progress.watch_seconds = max(progress.watch_seconds or 0, watch_seconds)
        if position_seconds is not None:
            progress.last_position_seconds = position_seconds
        if completed is not None and completed and not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.now(UTC)

        enrollment.last_lesson_id = lesson.id
        if enrollment.started_at is None:
            enrollment.started_at = datetime.now(UTC)

        await self.db.commit()

        certificate_issued = await self.recalculate_enrollment(enrollment.id, course=course)
        await self.db.refresh(enrollment)
        await self.db.refresh(progress)

        next_lesson_id = self._next_lesson_id(course, lesson.id)
        return progress, enrollment, next_lesson_id, certificate_issued

    async def _assert_previous_completed(
        self, enrollment: Enrollment, course: Course, lesson: Lesson
    ) -> None:
        ordered = _flatten(course)
        try:
            index = [item.id for item in ordered].index(lesson.id)
        except ValueError:
            return
        if index == 0:
            return

        previous_ids = [item.id for item in ordered[:index]]
        done = await self.db.scalar(
            select(func.count(LessonProgress.id)).where(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.lesson_id.in_(previous_ids),
                LessonProgress.completed.is_(True),
            )
        )
        if int(done or 0) < len(previous_ids):
            raise ConflictError("Bu kursda darslar ketma-ket o'tilishi kerak")

    @staticmethod
    def _next_lesson_id(course: Course, current_id: uuid.UUID) -> uuid.UUID | None:
        ordered = [item.id for item in _flatten(course)]
        try:
            index = ordered.index(current_id)
        except ValueError:
            return None
        return ordered[index + 1] if index + 1 < len(ordered) else None

    async def locked_lesson_ids(self, enrollment: Enrollment, course: Course) -> set[uuid.UUID]:
        if not course.sequential_progress:
            return set()

        completed = set(
            (
                await self.db.scalars(
                    select(LessonProgress.lesson_id).where(
                        LessonProgress.enrollment_id == enrollment.id,
                        LessonProgress.completed.is_(True),
                    )
                )
            ).all()
        )
        locked: set[uuid.UUID] = set()
        blocked = False
        for lesson in _flatten(course):
            if blocked:
                locked.add(lesson.id)
            elif lesson.id not in completed:
                blocked = True
        return locked

    async def recalculate_enrollment(
        self, enrollment_id: uuid.UUID, course: Course | None = None
    ) -> bool:
        enrollment = await self.db.scalar(
            select(Enrollment)
            .where(Enrollment.id == enrollment_id)
            .options(selectinload(Enrollment.certificate))
        )
        if enrollment is None:
            return False

        if course is None:
            course = await self.load_course_for_learning(enrollment.course_id)

        total_lessons = len(_flatten(course))
        completed_lessons = int(
            await self.db.scalar(
                select(func.count(LessonProgress.id)).where(
                    LessonProgress.enrollment_id == enrollment.id,
                    LessonProgress.completed.is_(True),
                )
            )
            or 0
        )

        percent = int(round(completed_lessons / total_lessons * 100)) if total_lessons else 0
        enrollment.completed_lessons = completed_lessons
        enrollment.progress_percent = min(percent, 100)

        certificate_started = False
        threshold = course.completion_threshold or 100
        quizzes_passed = await self._required_quizzes_passed(enrollment, course)

        if percent >= threshold and quizzes_passed:
            if enrollment.status is not EnrollmentStatus.completed:
                enrollment.status = EnrollmentStatus.completed
                enrollment.completed_at = datetime.now(UTC)
                logger.info("Kurs tugallandi: enrollment=%s", enrollment.id)

            if course.has_certificate and enrollment.certificate is None:
                certificate_started = _queue_certificate(enrollment.id)

        await self.db.commit()

        _queue_crm_progress(enrollment.id)
        return certificate_started

    async def _required_quizzes_passed(self, enrollment: Enrollment, course: Course) -> bool:
        quiz_ids = [
            lesson.quiz.id
            for lesson in _flatten(course)
            if lesson.quiz is not None and lesson.is_published
        ]
        if not quiz_ids:
            return True

        passed = set(
            (
                await self.db.scalars(
                    select(QuizAttempt.quiz_id).where(
                        QuizAttempt.user_id == enrollment.user_id,
                        QuizAttempt.quiz_id.in_(quiz_ids),
                        QuizAttempt.passed.is_(True),
                    )
                )
            ).all()
        )
        return len(passed) >= len(quiz_ids)


class QuizService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_quiz(self, lesson_id: uuid.UUID) -> Quiz:
        quiz = await self.db.scalar(select(Quiz).where(Quiz.lesson_id == lesson_id))
        if quiz is None:
            raise NotFoundError("Bu darsda test yo'q")
        return quiz

    async def attempts_info(self, user: User, quiz: Quiz) -> tuple[int, int | None, bool]:
        rows = list(
            (
                await self.db.scalars(
                    select(QuizAttempt).where(
                        QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user.id
                    )
                )
            ).all()
        )
        best = max((row.score for row in rows), default=None)
        passed = any(row.passed for row in rows)
        return len(rows), best, passed

    async def submit(
        self, user: User, lesson_id: uuid.UUID, answers: dict[str, list[str]]
    ) -> tuple[QuizAttempt, Quiz, list[dict]]:
        quiz = await self.get_quiz(lesson_id)

        lesson = await self.db.scalar(
            select(Lesson).where(Lesson.id == lesson_id).options(selectinload(Lesson.module))
        )
        if lesson is None:
            raise NotFoundError("Dars topilmadi")

        enrollment = await self.db.scalar(
            select(Enrollment).where(
                Enrollment.user_id == user.id, Enrollment.course_id == lesson.module.course_id
            )
        )
        if enrollment is None:
            raise PermissionDeniedError("Testdan o'tish uchun kursga yozilishingiz kerak")

        attempts_used, _, _ = await self.attempts_info(user, quiz)
        if quiz.max_attempts and attempts_used >= quiz.max_attempts:
            raise ConflictError(f"Urinishlar chegarasi tugagan ({quiz.max_attempts})")

        questions = quiz.questions or []
        total_points = sum(int(q.get("points", 1)) for q in questions) or 1
        earned = 0
        correct_count = 0
        details: list[dict] = []

        for question in questions:
            qid = str(question.get("id"))
            correct = {str(c) for c in (question.get("correct") or [])}
            given = {str(a) for a in (answers.get(qid) or [])}
            is_correct = bool(correct) and given == correct
            if is_correct:
                earned += int(question.get("points", 1))
                correct_count += 1
            details.append(
                {
                    "question_id": qid,
                    "correct": is_correct,
                    "correct_answers": sorted(correct),
                    "given_answers": sorted(given),
                }
            )

        score = int(round(earned / total_points * 100))
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user.id,
            enrollment_id=enrollment.id,
            score=score,
            passed=score >= quiz.passing_score,
            answers=answers,
            attempt_number=attempts_used + 1,
        )
        self.db.add(attempt)

        if attempt.passed:
            progress = await self.db.scalar(
                select(LessonProgress).where(
                    LessonProgress.enrollment_id == enrollment.id,
                    LessonProgress.lesson_id == lesson.id,
                )
            )
            if progress is None:
                progress = LessonProgress(
                    enrollment_id=enrollment.id,
                    lesson_id=lesson.id,
                    completed=False,
                    watch_seconds=0,
                    last_position_seconds=0,
                )
                self.db.add(progress)
            if not progress.completed:
                progress.completed = True
                progress.completed_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt, quiz, details

    async def upsert_quiz(self, lesson: Lesson, payload) -> Quiz:
        questions = []
        for index, question in enumerate(payload.questions, start=1):
            option_ids = {option.id for option in question.options}
            unknown = set(question.correct) - option_ids
            if unknown:
                raise ValidationError(
                    f"{index}-savolda to'g'ri javob variantlar ichida yo'q: {', '.join(unknown)}"
                )
            questions.append(
                {
                    "id": question.id or f"q{index}",
                    "text": question.text,
                    "type": question.type,
                    "options": [option.model_dump() for option in question.options],
                    "correct": question.correct,
                    "points": question.points,
                }
            )

        quiz = await self.db.scalar(select(Quiz).where(Quiz.lesson_id == lesson.id))
        if quiz is None:
            quiz = Quiz(lesson_id=lesson.id)
            self.db.add(quiz)

        quiz.title = payload.title
        quiz.passing_score = payload.passing_score
        quiz.max_attempts = payload.max_attempts
        quiz.time_limit_minutes = payload.time_limit_minutes
        quiz.shuffle_questions = payload.shuffle_questions
        quiz.questions = questions

        await self.db.commit()
        await self.db.refresh(quiz)
        return quiz


def _flatten(course: Course) -> list[Lesson]:
    lessons: list[Lesson] = []
    for module in sorted(course.modules, key=lambda m: m.order_index):
        lessons.extend(
            sorted(
                (lesson for lesson in module.lessons if lesson.is_published),
                key=lambda lesson: lesson.order_index,
            )
        )
    return lessons


def _queue_certificate(enrollment_id: uuid.UUID) -> bool:
    try:
        from app.worker.tasks.certificates import issue_certificate

        issue_certificate.delay(str(enrollment_id))
        return True
    except Exception as exc:
        logger.warning("Sertifikat job navbatga qo'yilmadi: %s", exc)
        return False


def _queue_crm_progress(enrollment_id: uuid.UUID) -> None:
    try:
        from app.worker.tasks.crm import sync_progress_to_crm

        sync_progress_to_crm.delay(str(enrollment_id))
    except Exception as exc:
        logger.debug("CRM progress job navbatga qo'yilmadi: %s", exc)


async def find_certificate(db: AsyncSession, enrollment_id: uuid.UUID) -> Certificate | None:
    return await db.scalar(select(Certificate).where(Certificate.enrollment_id == enrollment_id))
