"""Progress, Course Player va quiz endpointlari."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, TeacherUser
from app.core.exceptions import NotFoundError
from app.models.enums import EnrollmentStatus
from app.models.learning import Enrollment
from app.modules.courses.mappers import to_course_card, to_lesson_detail
from app.modules.courses.schemas import ModuleDetail
from app.modules.courses.service import CourseAuthoringService
from app.modules.progress.schemas import (
    EnrollmentView,
    LearnCourseView,
    ProgressUpdateRequest,
    ProgressUpdateResponse,
    QuizPublic,
    QuizQuestionPublic,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizUpsert,
)
from app.modules.progress.service import ProgressService, QuizService

router = APIRouter(tags=["Learning"])


# ===================================================================
#  Enrollmentlar
# ===================================================================
@router.get("/enrollments/me", response_model=list[EnrollmentView], summary="Mening kurslarim")
async def my_enrollments(
    user: CurrentUser,
    db: DbSession,
    enrollment_status: EnrollmentStatus | None = None,
) -> list[EnrollmentView]:
    enrollments = await ProgressService(db).list_enrollments(user, enrollment_status)
    result = []
    for enrollment in enrollments:
        view = EnrollmentView.model_validate(
            {
                **{
                    field: getattr(enrollment, field)
                    for field in (
                        "id",
                        "status",
                        "source",
                        "progress_percent",
                        "completed_lessons",
                        "last_lesson_id",
                        "enrolled_at",
                        "completed_at",
                    )
                },
                "course": to_course_card(enrollment.course, is_enrolled=True),
                "has_certificate": enrollment.certificate is not None,
            }
        )
        result.append(view)
    return result


# ===================================================================
#  Course Player
# ===================================================================
@router.get(
    "/learn/{course_id}",
    response_model=LearnCourseView,
    summary="Videodarslik sahifasi uchun ma'lumot",
)
async def learn_course(course_id: uuid.UUID, user: CurrentUser, db: DbSession) -> LearnCourseView:
    service = ProgressService(db)
    enrollment = await service.get_enrollment(user, course_id)
    course = await service.load_course_for_learning(course_id)

    progress_rows = await service.progress_rows(enrollment.id)
    progress_by_lesson = {row.lesson_id: row for row in progress_rows}
    locked = await service.locked_lesson_ids(enrollment, course)

    modules: list[ModuleDetail] = []
    total_lessons = 0
    for module in sorted(course.modules, key=lambda m: m.order_index):
        lessons = sorted(
            (lesson for lesson in module.lessons if lesson.is_published),
            key=lambda lesson: lesson.order_index,
        )
        total_lessons += len(lessons)
        modules.append(
            ModuleDetail(
                id=module.id,
                title=module.title,
                description=module.description,
                order_index=module.order_index,
                lessons=[
                    to_lesson_detail(
                        lesson,
                        progress_by_lesson.get(lesson.id),
                        is_locked=lesson.id in locked,
                    )
                    for lesson in lessons
                ],
            )
        )

    current_lesson_id = enrollment.last_lesson_id
    if current_lesson_id is None and modules and modules[0].lessons:
        current_lesson_id = modules[0].lessons[0].id

    certificate = enrollment.certificate
    return LearnCourseView(
        enrollment_id=enrollment.id,
        course=to_course_card(course, is_enrolled=True),
        progress_percent=enrollment.progress_percent,
        completed_lessons=enrollment.completed_lessons,
        total_lessons=total_lessons,
        modules=modules,
        current_lesson_id=current_lesson_id,
        sequential_progress=course.sequential_progress,
        certificate_code=certificate.certificate_code if certificate else None,
    )


@router.post(
    "/enrollments/{enrollment_id}/progress",
    response_model=ProgressUpdateResponse,
    summary="Dars progressini saqlash (debounce bilan har 10-15 sek)",
)
async def update_progress(
    enrollment_id: uuid.UUID,
    payload: ProgressUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> ProgressUpdateResponse:
    progress, enrollment, next_lesson_id, certificate_issued = await ProgressService(
        db
    ).update_progress(
        user,
        enrollment_id,
        payload.lesson_id,
        watch_seconds=payload.watch_seconds,
        position_seconds=payload.position_seconds,
        completed=payload.completed,
    )
    return ProgressUpdateResponse(
        lesson_id=progress.lesson_id,
        completed=progress.completed,
        watch_seconds=progress.watch_seconds,
        last_position_seconds=progress.last_position_seconds,
        course_progress_percent=enrollment.progress_percent,
        course_completed=enrollment.status is EnrollmentStatus.completed,
        next_lesson_id=next_lesson_id,
        certificate_issued=certificate_issued,
    )


# ===================================================================
#  Quiz — talaba
# ===================================================================
@router.get("/lessons/{lesson_id}/quiz", response_model=QuizPublic, summary="Testni olish")
async def get_quiz(lesson_id: uuid.UUID, user: CurrentUser, db: DbSession) -> QuizPublic:
    service = QuizService(db)
    quiz = await service.get_quiz(lesson_id)
    attempts_used, best_score, passed = await service.attempts_info(user, quiz)

    questions = [
        QuizQuestionPublic(
            id=str(q.get("id")),
            text=q.get("text", ""),
            type=q.get("type", "single"),
            options=q.get("options", []),
            points=int(q.get("points", 1)),
        )
        for q in (quiz.questions or [])
    ]
    return QuizPublic(
        id=quiz.id,
        lesson_id=quiz.lesson_id,
        title=quiz.title,
        passing_score=quiz.passing_score,
        max_attempts=quiz.max_attempts,
        time_limit_minutes=quiz.time_limit_minutes,
        questions=questions,
        attempts_used=attempts_used,
        best_score=best_score,
        passed=passed,
    )


@router.post(
    "/lessons/{lesson_id}/quiz/submit",
    response_model=QuizSubmitResponse,
    summary="Testni topshirish",
)
async def submit_quiz(
    lesson_id: uuid.UUID,
    payload: QuizSubmitRequest,
    user: CurrentUser,
    db: DbSession,
) -> QuizSubmitResponse:
    quiz_service = QuizService(db)
    attempt, quiz, details = await quiz_service.submit(user, lesson_id, payload.answers)

    # Progressni qayta hisoblaymiz (test o'tilgan bo'lsa dars ham tugadi)
    progress_service = ProgressService(db)
    enrollment = await db.scalar(select(Enrollment).where(Enrollment.id == attempt.enrollment_id))
    certificate_issued = False
    percent = 0
    if enrollment is not None:
        certificate_issued = await progress_service.recalculate_enrollment(enrollment.id)
        await db.refresh(enrollment)
        percent = enrollment.progress_percent

    return QuizSubmitResponse(
        score=attempt.score,
        passed=attempt.passed,
        passing_score=quiz.passing_score,
        correct_count=sum(1 for d in details if d["correct"]),
        total_questions=len(details),
        attempt_number=attempt.attempt_number,
        details=details,
        course_progress_percent=percent,
        certificate_issued=certificate_issued,
    )


# ===================================================================
#  Quiz — teacher
# ===================================================================
@router.put(
    "/teacher/lessons/{lesson_id}/quiz",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Darsga test yaratish/tahrirlash",
)
async def upsert_quiz(
    lesson_id: uuid.UUID,
    payload: QuizUpsert,
    user: TeacherUser,
    db: DbSession,
) -> dict:
    lesson = await CourseAuthoringService(db).get_lesson_for_edit(user, lesson_id)
    quiz = await QuizService(db).upsert_quiz(lesson, payload)
    return {
        "id": str(quiz.id),
        "lesson_id": str(quiz.lesson_id),
        "questions_count": len(quiz.questions or []),
        "passing_score": quiz.passing_score,
    }


@router.get(
    "/teacher/lessons/{lesson_id}/quiz",
    response_model=dict,
    summary="Testni to'g'ri javoblari bilan olish (teacher)",
)
async def get_quiz_for_edit(lesson_id: uuid.UUID, user: TeacherUser, db: DbSession) -> dict:
    lesson = await CourseAuthoringService(db).get_lesson_for_edit(user, lesson_id)
    if lesson.quiz is None:
        raise NotFoundError("Bu darsda test yo'q")
    quiz = lesson.quiz
    return {
        "id": str(quiz.id),
        "lesson_id": str(quiz.lesson_id),
        "title": quiz.title,
        "passing_score": quiz.passing_score,
        "max_attempts": quiz.max_attempts,
        "time_limit_minutes": quiz.time_limit_minutes,
        "shuffle_questions": quiz.shuffle_questions,
        "questions": quiz.questions,
    }
