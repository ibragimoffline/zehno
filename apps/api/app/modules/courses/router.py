"""Kurs katalogi (ochiq), CMS (teacher) va moderatsiya (admin) endpointlari."""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Query, status
from slugify import slugify
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.core.deps import (
    AdminUser,
    CurrentUser,
    DbSession,
    OptionalUser,
    PaginationDep,
    TeacherUser,
)
from app.core.exceptions import ConflictError, NotFoundError
from app.models.catalog import Category, Course, CourseModule, Lesson, ModerationLog
from app.models.enums import (
    CourseLevel,
    CourseStatus,
    EnrollmentStatus,
    ModerationAction,
    UserRole,
)
from app.models.learning import Enrollment
from app.modules.courses.mappers import (
    to_course_card,
    to_course_detail,
    to_module_public,
)
from app.modules.courses.schemas import (
    CategoryCreate,
    CategoryPublic,
    CourseAdminDetail,
    CourseAdminSummary,
    CourseCard,
    CourseCreate,
    CourseDetail,
    CourseOwner,
    CourseUpdate,
    LessonCreate,
    LessonPublic,
    LessonUpdate,
    ModerationLogView,
    ModerationRejection,
    ModuleCreate,
    ModulePublic,
    ModuleUpdate,
    ReorderRequest,
    ReviewCreate,
    ReviewPublic,
    TeacherStudentRow,
)
from app.modules.courses.service import CatalogService, CourseAuthoringService, ReviewService
from app.schemas.common import Message, Page

router = APIRouter(tags=["Courses"])


# ===================================================================
#  Kategoriyalar
# ===================================================================
@router.get("/categories", response_model=list[CategoryPublic], summary="Kategoriyalar")
async def list_categories(db: DbSession) -> list[CategoryPublic]:
    result = []
    for category, count in await CatalogService(db).list_categories():
        item = CategoryPublic.model_validate(category)
        item.courses_count = count
        result.append(item)
    return result


@router.post(
    "/categories",
    response_model=CategoryPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Kategoriya yaratish (admin)",
)
async def create_category(payload: CategoryCreate, _: AdminUser, db: DbSession) -> CategoryPublic:
    slug = slugify(payload.name)[:140]
    if await db.scalar(select(Category.id).where(Category.slug == slug)):
        raise ConflictError("Bunday kategoriya allaqachon mavjud")
    category = Category(slug=slug, **payload.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return CategoryPublic.model_validate(category)


# ===================================================================
#  Ochiq katalog
# ===================================================================
@router.get("/courses", response_model=Page[CourseCard], summary="Kurs katalogi")
async def list_courses(
    db: DbSession,
    pagination: PaginationDep,
    user: OptionalUser,
    search: str | None = Query(default=None, description="Qidiruv matni"),
    category: str | None = Query(default=None, description="Kategoriya slug'i"),
    level: CourseLevel | None = None,
    language: str | None = Query(default=None, max_length=5),
    price_min: Decimal | None = Query(default=None, ge=0),
    price_max: Decimal | None = Query(default=None, ge=0),
    is_free: bool | None = None,
    min_rating: float | None = Query(default=None, ge=0, le=5),
    teacher_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    featured: bool | None = None,
    sort: str = Query(default="newest", pattern="^(newest|popular|rating|price_asc|price_desc)$"),
) -> Page[CourseCard]:
    service = CatalogService(db)
    courses, total = await service.search_courses(
        pagination,
        search=search,
        category_slug=category,
        level=level,
        language=language,
        price_min=price_min,
        price_max=price_max,
        is_free=is_free,
        min_rating=min_rating,
        owner_id=teacher_id,
        organization_id=organization_id,
        featured=featured,
        sort=sort,
    )
    enrolled = await service.enrolled_course_ids(user.id if user else None, [c.id for c in courses])
    items = [to_course_card(c, is_enrolled=c.id in enrolled) for c in courses]
    return Page.build(items, total, pagination.page, pagination.per_page)


@router.get(
    "/courses/featured",
    response_model=list[CourseCard],
    summary="Bosh sahifa uchun tanlangan kurslar",
)
async def featured_courses(db: DbSession, user: OptionalUser, limit: int = Query(8, ge=1, le=24)):
    from app.core.deps import Pagination

    service = CatalogService(db)
    courses, _ = await service.search_courses(Pagination(page=1, per_page=limit), sort="popular")
    enrolled = await service.enrolled_course_ids(user.id if user else None, [c.id for c in courses])
    return [to_course_card(c, is_enrolled=c.id in enrolled) for c in courses]


@router.get("/courses/{slug_or_id}", response_model=CourseDetail, summary="Kurs tafsiloti")
async def get_course(slug_or_id: str, db: DbSession, user: OptionalUser) -> CourseDetail:
    service = CatalogService(db)
    course = await service.get_public_course(slug_or_id)
    is_enrolled = await service.is_enrolled(user.id if user else None, course.id)
    return to_course_detail(course, is_enrolled=is_enrolled)


@router.get(
    "/courses/{course_id}/reviews",
    response_model=Page[ReviewPublic],
    summary="Kurs sharhlari",
)
async def list_reviews(
    course_id: uuid.UUID, db: DbSession, pagination: PaginationDep
) -> Page[ReviewPublic]:
    reviews, total = await ReviewService(db).list_reviews(course_id, pagination)
    return Page.build(
        [ReviewPublic.model_validate(r) for r in reviews],
        total,
        pagination.page,
        pagination.per_page,
    )


@router.post(
    "/courses/{course_id}/reviews",
    response_model=ReviewPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Sharh qoldirish",
)
async def add_review(
    course_id: uuid.UUID,
    payload: ReviewCreate,
    user: CurrentUser,
    db: DbSession,
) -> ReviewPublic:
    review = await ReviewService(db).add_review(user, course_id, payload.rating, payload.comment)
    return ReviewPublic.model_validate(review)


# ===================================================================
#  Teacher CMS
# ===================================================================
@router.get(
    "/teacher/courses",
    response_model=Page[CourseAdminSummary],
    summary="Mening kurslarim (teacher)",
)
async def my_courses(
    user: TeacherUser,
    db: DbSession,
    pagination: PaginationDep,
    course_status: CourseStatus | None = Query(default=None, alias="status"),
) -> Page[CourseAdminSummary]:
    service = CourseAuthoringService(db)
    courses, total = await service.list_own_courses(user, pagination, course_status)
    items = [CourseAdminSummary.model_validate(c) for c in courses]
    for item, course in zip(items, courses, strict=True):
        item.owner = CourseOwner.model_validate(course.owner) if course.owner else None
    return Page.build(items, total, pagination.page, pagination.per_page)


@router.post(
    "/teacher/courses",
    response_model=CourseAdminSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Kurs yaratish (wizard 1-qadam)",
)
async def create_course(
    payload: CourseCreate, user: TeacherUser, db: DbSession
) -> CourseAdminSummary:
    course = await CourseAuthoringService(db).create_course(user, payload)
    return CourseAdminSummary.model_validate(course)


@router.get(
    "/teacher/courses/{course_id}",
    response_model=CourseAdminDetail,
    summary="Kursni tahrirlash uchun olish",
)
async def get_own_course(
    course_id: uuid.UUID, user: TeacherUser, db: DbSession
) -> CourseAdminDetail:
    course = await db.scalar(
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
    CourseAuthoringService.assert_can_edit(user, course)

    detail = CourseAdminDetail.model_validate(course)
    detail.modules = sorted(
        (to_module_public(m) for m in course.modules), key=lambda m: m.order_index
    )
    return detail


@router.patch(
    "/teacher/courses/{course_id}",
    response_model=CourseAdminSummary,
    summary="Kursni tahrirlash",
)
async def update_course(
    course_id: uuid.UUID, payload: CourseUpdate, user: TeacherUser, db: DbSession
) -> CourseAdminSummary:
    course = await CourseAuthoringService(db).update_course(user, course_id, payload)
    return CourseAdminSummary.model_validate(course)


@router.delete("/teacher/courses/{course_id}", response_model=Message, summary="Kursni o'chirish")
async def delete_course(course_id: uuid.UUID, user: TeacherUser, db: DbSession) -> Message:
    await CourseAuthoringService(db).delete_course(user, course_id)
    return Message(message="Kurs o'chirildi")


@router.post(
    "/teacher/courses/{course_id}/submit",
    response_model=CourseAdminSummary,
    summary="Moderatsiyaga yuborish (wizard oxirgi qadam)",
)
async def submit_course(
    course_id: uuid.UUID, user: TeacherUser, db: DbSession
) -> CourseAdminSummary:
    course = await CourseAuthoringService(db).submit_for_review(user, course_id)
    return CourseAdminSummary.model_validate(course)


# ---------------------------------------------------------------- modullar
@router.post(
    "/teacher/courses/{course_id}/modules",
    response_model=ModulePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Modul qo'shish",
)
async def create_module(
    course_id: uuid.UUID, payload: ModuleCreate, user: TeacherUser, db: DbSession
) -> ModulePublic:
    module = await CourseAuthoringService(db).create_module(user, course_id, payload)
    return ModulePublic.model_validate(module)


@router.patch(
    "/teacher/modules/{module_id}", response_model=ModulePublic, summary="Modulni tahrirlash"
)
async def update_module(
    module_id: uuid.UUID, payload: ModuleUpdate, user: TeacherUser, db: DbSession
) -> ModulePublic:
    module = await CourseAuthoringService(db).update_module(user, module_id, payload)
    return ModulePublic.model_validate(module)


@router.delete("/teacher/modules/{module_id}", response_model=Message, summary="Modulni o'chirish")
async def delete_module(module_id: uuid.UUID, user: TeacherUser, db: DbSession) -> Message:
    await CourseAuthoringService(db).delete_module(user, module_id)
    return Message(message="Modul o'chirildi")


@router.put(
    "/teacher/courses/{course_id}/modules/reorder",
    response_model=list[ModulePublic],
    summary="Modullar tartibini o'zgartirish (drag & drop)",
)
async def reorder_modules(
    course_id: uuid.UUID, payload: ReorderRequest, user: TeacherUser, db: DbSession
) -> list[ModulePublic]:
    modules = await CourseAuthoringService(db).reorder_modules(user, course_id, payload)
    return [ModulePublic.model_validate(m) for m in modules]


# ---------------------------------------------------------------- darslar
@router.post(
    "/teacher/modules/{module_id}/lessons",
    response_model=LessonPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Dars qo'shish",
)
async def create_lesson(
    module_id: uuid.UUID, payload: LessonCreate, user: TeacherUser, db: DbSession
) -> LessonPublic:
    lesson = await CourseAuthoringService(db).create_lesson(user, module_id, payload)
    return LessonPublic.model_validate(lesson)


@router.patch(
    "/teacher/lessons/{lesson_id}", response_model=LessonPublic, summary="Darsni tahrirlash"
)
async def update_lesson(
    lesson_id: uuid.UUID, payload: LessonUpdate, user: TeacherUser, db: DbSession
) -> LessonPublic:
    lesson = await CourseAuthoringService(db).update_lesson(user, lesson_id, payload)
    return LessonPublic.model_validate(lesson)


@router.delete("/teacher/lessons/{lesson_id}", response_model=Message, summary="Darsni o'chirish")
async def delete_lesson(lesson_id: uuid.UUID, user: TeacherUser, db: DbSession) -> Message:
    await CourseAuthoringService(db).delete_lesson(user, lesson_id)
    return Message(message="Dars o'chirildi")


@router.get(
    "/teacher/students",
    response_model=Page[TeacherStudentRow],
    summary="Kurslarimga yozilgan talabalar (teacher)",
)
async def teacher_students(
    user: TeacherUser,
    db: DbSession,
    pagination: PaginationDep,
    course_id: uuid.UUID | None = None,
    enrollment_status: EnrollmentStatus | None = None,
) -> Page[TeacherStudentRow]:
    """Ustoz faqat o'zi (yoki tashkiloti) egasi bo'lgan kurslardagi talabalarni ko'radi."""
    owned = select(Course.id).where(Course.owner_id == user.id)
    if user.role is UserRole.org_admin and user.organization_id:
        owned = select(Course.id).where(
            or_(Course.owner_id == user.id, Course.organization_id == user.organization_id)
        )
    elif user.role is UserRole.admin:
        owned = select(Course.id)

    stmt = (
        select(Enrollment)
        .where(Enrollment.course_id.in_(owned))
        .options(selectinload(Enrollment.user), selectinload(Enrollment.course))
    )
    if course_id:
        stmt = stmt.where(Enrollment.course_id == course_id)
    if enrollment_status:
        stmt = stmt.where(Enrollment.status == enrollment_status)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(Enrollment.enrolled_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )

    items: list[TeacherStudentRow] = []
    for enrollment in rows.all():
        item = TeacherStudentRow.model_validate(enrollment)
        item.user_name = enrollment.user.full_name if enrollment.user else None
        item.user_email = enrollment.user.email if enrollment.user else None
        item.course_title = enrollment.course.title if enrollment.course else None
        items.append(item)

    return Page.build(items, int(total), pagination.page, pagination.per_page)


@router.put(
    "/teacher/modules/{module_id}/lessons/reorder",
    response_model=list[LessonPublic],
    summary="Darslar tartibini o'zgartirish (drag & drop)",
)
async def reorder_lessons(
    module_id: uuid.UUID, payload: ReorderRequest, user: TeacherUser, db: DbSession
) -> list[LessonPublic]:
    lessons = await CourseAuthoringService(db).reorder_lessons(user, module_id, payload)
    return [LessonPublic.model_validate(lesson) for lesson in lessons]


# ===================================================================
#  Moderatsiya (super-admin)
# ===================================================================
@router.get(
    "/admin/moderation/pending-courses",
    response_model=Page[CourseAdminSummary],
    summary="Moderatsiya kutayotgan kurslar",
)
async def pending_courses(
    _: AdminUser, db: DbSession, pagination: PaginationDep
) -> Page[CourseAdminSummary]:
    courses, total = await CourseAuthoringService(db).pending_courses(pagination)
    return Page.build(
        [CourseAdminSummary.model_validate(c) for c in courses],
        total,
        pagination.page,
        pagination.per_page,
    )


@router.post(
    "/admin/moderation/{course_id}/approve",
    response_model=CourseAdminSummary,
    summary="Kursni tasdiqlash",
)
async def approve_course(
    course_id: uuid.UUID,
    admin: AdminUser,
    db: DbSession,
    comment: str | None = None,
) -> CourseAdminSummary:
    course = await CourseAuthoringService(db).moderate(
        admin, course_id, ModerationAction.approve, comment
    )
    return CourseAdminSummary.model_validate(course)


@router.post(
    "/admin/moderation/{course_id}/reject",
    response_model=CourseAdminSummary,
    summary="Kursni rad etish",
)
async def reject_course(
    course_id: uuid.UUID,
    payload: ModerationRejection,
    admin: AdminUser,
    db: DbSession,
) -> CourseAdminSummary:
    course = await CourseAuthoringService(db).moderate(
        admin, course_id, ModerationAction.reject, payload.reason
    )
    return CourseAdminSummary.model_validate(course)


@router.get(
    "/admin/moderation/logs",
    response_model=Page[ModerationLogView],
    summary="Moderatsiya loglari",
)
async def moderation_logs(
    _: AdminUser,
    db: DbSession,
    pagination: PaginationDep,
    course_id: uuid.UUID | None = None,
) -> Page[ModerationLogView]:
    stmt = select(ModerationLog)
    if course_id:
        stmt = stmt.where(ModerationLog.course_id == course_id)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(ModerationLog.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    return Page.build(
        [ModerationLogView.model_validate(r) for r in rows.all()],
        total,
        pagination.page,
        pagination.per_page,
    )
