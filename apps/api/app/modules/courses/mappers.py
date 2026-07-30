"""ORM → Pydantic konverterlar (kurs kartochkasi, modul/dars daraxti)."""

from __future__ import annotations

import uuid

from app.models.catalog import Course, CourseModule, Lesson
from app.models.learning import LessonProgress
from app.modules.courses.schemas import (
    CategoryPublic,
    CourseCard,
    CourseDetail,
    CourseOwner,
    LessonDetail,
    LessonPublic,
    ModulePublic,
    VideoAssetPublic,
)


def to_course_card(course: Course, *, is_enrolled: bool = False) -> CourseCard:
    card = CourseCard.model_validate(course)
    card.owner = CourseOwner.model_validate(course.owner) if course.owner else None
    card.category = CategoryPublic.model_validate(course.category) if course.category else None
    card.is_enrolled = is_enrolled
    return card


def to_lesson_public(lesson: Lesson) -> LessonPublic:
    item = LessonPublic.model_validate(lesson)
    item.has_video = lesson.video_asset is not None
    item.has_quiz = lesson.quiz is not None
    return item


def to_module_public(module: CourseModule) -> ModulePublic:
    lessons = [to_lesson_public(lesson) for lesson in module.lessons if lesson.is_published]
    item = ModulePublic.model_validate(module)
    item.lessons = sorted(lessons, key=lambda lesson: lesson.order_index)
    item.duration_seconds = sum(lesson.duration_seconds for lesson in lessons)
    return item


def to_course_detail(course: Course, *, is_enrolled: bool = False) -> CourseDetail:
    detail = CourseDetail.model_validate(course)
    detail.owner = CourseOwner.model_validate(course.owner) if course.owner else None
    detail.category = CategoryPublic.model_validate(course.category) if course.category else None
    detail.is_enrolled = is_enrolled
    detail.modules = sorted(
        (to_module_public(module) for module in course.modules),
        key=lambda module: module.order_index,
    )
    return detail


def to_lesson_detail(
    lesson: Lesson,
    progress: LessonProgress | None = None,
    *,
    is_locked: bool = False,
) -> LessonDetail:
    detail = LessonDetail.model_validate(lesson)
    detail.has_video = lesson.video_asset is not None
    detail.has_quiz = lesson.quiz is not None
    detail.video = (
        VideoAssetPublic.model_validate(lesson.video_asset) if lesson.video_asset else None
    )
    if progress is not None:
        detail.completed = progress.completed
        detail.watch_seconds = progress.watch_seconds
        detail.last_position_seconds = progress.last_position_seconds
    detail.is_locked = is_locked
    return detail


def flatten_lessons(course: Course) -> list[Lesson]:
    """Kursning barcha darslarini tartib bo'yicha tekis ro'yxatga aylantiradi."""
    lessons: list[Lesson] = []
    for module in sorted(course.modules, key=lambda m: m.order_index):
        lessons.extend(sorted(module.lessons, key=lambda lesson: lesson.order_index))
    return lessons


def progress_map(rows: list[LessonProgress]) -> dict[uuid.UUID, LessonProgress]:
    return {row.lesson_id: row for row in rows}
