from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from slugify import slugify
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import Pagination
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from app.core.security import generate_code
from app.models.catalog import (
    Category,
    Course,
    CourseModule,
    CourseReview,
    Lesson,
    ModerationLog,
    VideoAsset,
)
from app.models.enums import (
    CourseLevel,
    CourseStatus,
    LessonContentType,
    ModerationAction,
    ReviewStatus,
    UserRole,
)
from app.models.learning import Enrollment, Quiz
from app.models.user import User
from app.modules.courses.schemas import (
    CourseCreate,
    CourseUpdate,
    LessonCreate,
    LessonUpdate,
    ModuleCreate,
    ModuleUpdate,
    ReorderRequest,
)

logger = logging.getLogger(__name__)

SORT_MAP = {
    "newest": (Course.published_at.desc().nullslast(), Course.created_at.desc()),
    "popular": (Course.students_count.desc(), Course.rating_avg.desc()),
    "rating": (Course.rating_avg.desc(), Course.rating_count.desc()),
    "price_asc": (Course.price.asc(),),
    "price_desc": (Course.price.desc(),),
}


class CatalogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_categories(self) -> list[tuple[Category, int]]:
        rows = await self.db.execute(
            select(Category, func.count(Course.id))
            .outerjoin(
                Course,
                (Course.category_id == Category.id) & (Course.status == CourseStatus.published),
            )
            .group_by(Category.id)
            .order_by(Category.order_index, Category.name)
        )
        return [(cat, int(count or 0)) for cat, count in rows.all()]

    async def search_courses(
        self,
        pagination: Pagination,
        *,
        search: str | None = None,
        category_slug: str | None = None,
        category_id: uuid.UUID | None = None,
        level: CourseLevel | None = None,
        language: str | None = None,
        price_min: Decimal | None = None,
        price_max: Decimal | None = None,
        is_free: bool | None = None,
        min_rating: float | None = None,
        owner_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        featured: bool | None = None,
        sort: str = "newest",
    ) -> tuple[list[Course], int]:
        stmt = (
            select(Course)
            .where(Course.status == CourseStatus.published)
            .options(
                selectinload(Course.owner),
                selectinload(Course.category),
            )
        )

        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Course.title).like(pattern),
                    func.lower(Course.subtitle).like(pattern),
                    func.lower(Course.description).like(pattern),
                )
            )
        if category_id:
            stmt = stmt.where(Course.category_id == category_id)
        elif category_slug:
            stmt = stmt.join(Category, Course.category_id == Category.id).where(
                Category.slug == category_slug
            )
        if level is not None:
            stmt = stmt.where(Course.level == level)
        if language:
            stmt = stmt.where(Course.language == language)
        if price_min is not None:
            stmt = stmt.where(Course.price >= price_min)
        if price_max is not None:
            stmt = stmt.where(Course.price <= price_max)
        if is_free is True:
            stmt = stmt.where(Course.price == 0)
        elif is_free is False:
            stmt = stmt.where(Course.price > 0)
        if min_rating is not None:
            stmt = stmt.where(Course.rating_avg >= min_rating)
        if owner_id:
            stmt = stmt.where(Course.owner_id == owner_id)
        if organization_id:
            stmt = stmt.where(Course.organization_id == organization_id)
        if featured is not None:
            stmt = stmt.where(Course.is_featured == featured)

        total = await self.db.scalar(
            select(func.count()).select_from(stmt.order_by(None).subquery())
        )
        order_by = SORT_MAP.get(sort, SORT_MAP["newest"])
        rows = await self.db.scalars(
            stmt.order_by(*order_by).offset(pagination.offset).limit(pagination.limit)
        )
        return list(rows.all()), int(total or 0)

    async def get_public_course(self, slug_or_id: str) -> Course:
        stmt = select(Course).options(
            selectinload(Course.owner),
            selectinload(Course.category),
            selectinload(Course.modules)
            .selectinload(CourseModule.lessons)
            .selectinload(Lesson.video_asset),
            selectinload(Course.modules)
            .selectinload(CourseModule.lessons)
            .selectinload(Lesson.quiz),
        )
        course = await self._resolve_course(stmt, slug_or_id)
        if course.status is not CourseStatus.published:
            raise NotFoundError("Kurs topilmadi yoki hali nashr etilmagan")
        return course

    async def _resolve_course(self, stmt, slug_or_id: str) -> Course:
        try:
            course_id = uuid.UUID(slug_or_id)
            course = await self.db.scalar(stmt.where(Course.id == course_id))
        except ValueError:
            course = await self.db.scalar(stmt.where(Course.slug == slug_or_id))
        if course is None:
            raise NotFoundError("Kurs topilmadi")
        return course

    async def is_enrolled(self, user_id: uuid.UUID | None, course_id: uuid.UUID) -> bool:
        if user_id is None:
            return False
        result = await self.db.scalar(
            select(Enrollment.id).where(
                Enrollment.user_id == user_id, Enrollment.course_id == course_id
            )
        )
        return result is not None

    async def enrolled_course_ids(
        self, user_id: uuid.UUID | None, course_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        if not user_id or not course_ids:
            return set()
        rows = await self.db.scalars(
            select(Enrollment.course_id).where(
                Enrollment.user_id == user_id, Enrollment.course_id.in_(course_ids)
            )
        )
        return set(rows.all())


class CourseAuthoringService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def assert_can_edit(user: User, course: Course) -> None:
        if user.role is UserRole.admin:
            return
        if course.owner_id == user.id:
            return
        if (
            user.role is UserRole.org_admin
            and course.organization_id is not None
            and course.organization_id == user.organization_id
        ):
            return
        raise PermissionDeniedError("Bu kursni tahrirlash huquqingiz yo'q")

    async def get_owned_course(self, user: User, course_id: uuid.UUID) -> Course:
        course = await self.db.scalar(
            select(Course)
            .where(Course.id == course_id)
            .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
        )
        if course is None:
            raise NotFoundError("Kurs topilmadi")
        self.assert_can_edit(user, course)
        return course

    async def create_course(self, user: User, payload: CourseCreate) -> Course:
        if not user.can_create_courses:
            raise PermissionDeniedError("Kurs yaratish uchun ustoz roli kerak")

        if payload.category_id:
            exists = await self.db.scalar(
                select(Category.id).where(Category.id == payload.category_id)
            )
            if exists is None:
                raise ValidationError("Bunday kategoriya mavjud emas")

        course = Course(
            owner_id=user.id,
            organization_id=user.organization_id,
            slug=await self._unique_slug(payload.title),
            status=CourseStatus.draft,
            **payload.model_dump(exclude={"category_id"}),
            category_id=payload.category_id,
        )
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course, ["owner", "category"])
        logger.info("Kurs yaratildi: %s (%s)", course.title, course.id)
        return course

    async def _unique_slug(self, title: str) -> str:
        base = slugify(title)[:200] or f"course-{generate_code(6, upper=False)}"
        slug, suffix = base, 1
        while await self.db.scalar(select(Course.id).where(Course.slug == slug)):
            suffix += 1
            slug = f"{base}-{suffix}"
        return slug

    async def update_course(
        self, user: User, course_id: uuid.UUID, payload: CourseUpdate
    ) -> Course:
        course = await self.get_owned_course(user, course_id)
        data = payload.model_dump(exclude_unset=True)

        if "title" in data and data["title"] and data["title"] != course.title:
            course.slug = await self._unique_slug(data["title"])

        price = data.get("price", course.price)
        discount = data.get("discount_price", course.discount_price)
        if discount is not None and price is not None and Decimal(discount) >= Decimal(price):
            raise ValidationError("Chegirma narxi asosiy narxdan kichik bo'lishi kerak")

        for field, value in data.items():
            setattr(course, field, value)

        await self.db.commit()
        await self.db.refresh(course, ["owner", "category"])
        return course

    async def delete_course(self, user: User, course_id: uuid.UUID) -> None:
        course = await self.get_owned_course(user, course_id)
        enrolled = await self.db.scalar(
            select(func.count(Enrollment.id)).where(Enrollment.course_id == course.id)
        )
        if enrolled:
            course.status = CourseStatus.archived
            await self.db.commit()
            raise ConflictError(
                f"Kursda {enrolled} ta talaba bor — kurs o'chirilmadi, arxivlandi",
                code="archived_instead",
            )
        await self.db.delete(course)
        await self.db.commit()

    async def list_own_courses(
        self, user: User, pagination: Pagination, status_filter: CourseStatus | None = None
    ) -> tuple[list[Course], int]:
        stmt = select(Course).options(selectinload(Course.category), selectinload(Course.owner))
        if user.role is UserRole.org_admin and user.organization_id:
            stmt = stmt.where(
                or_(Course.owner_id == user.id, Course.organization_id == user.organization_id)
            )
        elif user.role is not UserRole.admin:
            stmt = stmt.where(Course.owner_id == user.id)

        if status_filter is not None:
            stmt = stmt.where(Course.status == status_filter)

        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = await self.db.scalars(
            stmt.order_by(Course.updated_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows.all()), int(total)

    async def create_module(
        self, user: User, course_id: uuid.UUID, payload: ModuleCreate
    ) -> CourseModule:
        course = await self.get_owned_course(user, course_id)
        order_index = payload.order_index
        if order_index is None:
            max_order = await self.db.scalar(
                select(func.max(CourseModule.order_index)).where(
                    CourseModule.course_id == course.id
                )
            )
            order_index = (max_order or -1) + 1

        module = CourseModule(
            course_id=course.id,
            title=payload.title,
            description=payload.description,
            order_index=order_index,
        )
        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module, ["lessons"])
        return module

    async def update_module(
        self, user: User, module_id: uuid.UUID, payload: ModuleUpdate
    ) -> CourseModule:
        module = await self._get_module(user, module_id)
        for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(module, field, value)
        await self.db.commit()
        await self.db.refresh(module, ["lessons"])
        return module

    async def delete_module(self, user: User, module_id: uuid.UUID) -> None:
        module = await self._get_module(user, module_id)
        course_id = module.course_id
        await self.db.delete(module)
        await self.db.commit()
        await self.recalculate_course_stats(course_id)

    async def _get_module(self, user: User, module_id: uuid.UUID) -> CourseModule:
        module = await self.db.scalar(
            select(CourseModule)
            .where(CourseModule.id == module_id)
            .options(selectinload(CourseModule.course))
        )
        if module is None:
            raise NotFoundError("Modul topilmadi")
        self.assert_can_edit(user, module.course)
        return module

    async def reorder_modules(
        self, user: User, course_id: uuid.UUID, payload: ReorderRequest
    ) -> list[CourseModule]:
        course = await self.get_owned_course(user, course_id)
        by_id = {m.id: m for m in course.modules}
        for item in payload.items:
            module = by_id.get(item.id)
            if module is None:
                raise ValidationError(f"Modul {item.id} bu kursga tegishli emas")
            module.order_index = item.order_index
        await self.db.commit()
        return sorted(course.modules, key=lambda m: m.order_index)

    async def create_lesson(
        self, user: User, module_id: uuid.UUID, payload: LessonCreate
    ) -> Lesson:
        module = await self._get_module(user, module_id)
        order_index = payload.order_index
        if order_index is None:
            max_order = await self.db.scalar(
                select(func.max(Lesson.order_index)).where(Lesson.module_id == module.id)
            )
            order_index = (max_order or -1) + 1

        lesson = Lesson(
            module_id=module.id,
            **payload.model_dump(exclude={"order_index"}),
            order_index=order_index,
        )
        self.db.add(lesson)
        await self.db.commit()
        await self.db.refresh(lesson)
        await self.recalculate_course_stats(module.course_id)
        return lesson

    async def update_lesson(
        self, user: User, lesson_id: uuid.UUID, payload: LessonUpdate
    ) -> Lesson:
        lesson = await self.get_lesson_for_edit(user, lesson_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(lesson, field, value)
        await self.db.commit()
        await self.db.refresh(lesson)
        await self.recalculate_course_stats(lesson.module.course_id)
        return lesson

    async def delete_lesson(self, user: User, lesson_id: uuid.UUID) -> None:
        lesson = await self.get_lesson_for_edit(user, lesson_id)
        course_id = lesson.module.course_id
        await self.db.delete(lesson)
        await self.db.commit()
        await self.recalculate_course_stats(course_id)

    async def get_lesson_for_edit(self, user: User, lesson_id: uuid.UUID) -> Lesson:
        lesson = await self.db.scalar(
            select(Lesson)
            .where(Lesson.id == lesson_id)
            .options(
                selectinload(Lesson.module).selectinload(CourseModule.course),
                selectinload(Lesson.video_asset),
                selectinload(Lesson.quiz),
            )
        )
        if lesson is None:
            raise NotFoundError("Dars topilmadi")
        self.assert_can_edit(user, lesson.module.course)
        return lesson

    async def reorder_lessons(
        self, user: User, module_id: uuid.UUID, payload: ReorderRequest
    ) -> list[Lesson]:
        module = await self._get_module(user, module_id)
        lessons = await self.db.scalars(select(Lesson).where(Lesson.module_id == module.id))
        by_id = {lesson.id: lesson for lesson in lessons.all()}
        for item in payload.items:
            lesson = by_id.get(item.id)
            if lesson is None:
                raise ValidationError(f"Dars {item.id} bu modulga tegishli emas")
            lesson.order_index = item.order_index
        await self.db.commit()
        return sorted(by_id.values(), key=lambda lesson: lesson.order_index)

    async def recalculate_course_stats(self, course_id: uuid.UUID) -> None:
        totals = (
            await self.db.execute(
                select(
                    func.count(Lesson.id),
                    func.coalesce(func.sum(Lesson.duration_seconds), 0),
                )
                .select_from(Lesson)
                .join(CourseModule, Lesson.module_id == CourseModule.id)
                .where(CourseModule.course_id == course_id, Lesson.is_published.is_(True))
            )
        ).one()

        course = await self.db.scalar(select(Course).where(Course.id == course_id))
        if course is None:
            return
        course.lessons_count = int(totals[0] or 0)
        course.duration_seconds = int(totals[1] or 0)
        await self.db.commit()

    async def submit_for_review(self, user: User, course_id: uuid.UUID) -> Course:
        course = await self.get_owned_course(user, course_id)
        if course.status in (CourseStatus.pending, CourseStatus.published):
            raise ConflictError("Kurs allaqachon moderatsiyada yoki nashr etilgan")

        await self._assert_publishable(course)

        previous = course.status
        course.status = CourseStatus.pending
        course.submitted_at = datetime.now(UTC)
        course.rejection_reason = None
        self.db.add(
            ModerationLog(
                course_id=course.id,
                actor_id=user.id,
                action=ModerationAction.submit,
                from_status=previous.value,
                to_status=CourseStatus.pending.value,
            )
        )
        await self.db.commit()
        await self.db.refresh(course, ["owner", "category"])
        return course

    async def _assert_publishable(self, course: Course) -> None:
        modules = await self.db.scalars(
            select(CourseModule).where(CourseModule.course_id == course.id)
        )
        module_ids = [m.id for m in modules.all()]
        if not module_ids:
            raise ValidationError("Kursda kamida bitta modul bo'lishi kerak")

        lessons_count = await self.db.scalar(
            select(func.count(Lesson.id)).where(Lesson.module_id.in_(module_ids))
        )
        if not lessons_count:
            raise ValidationError("Kursda kamida bitta dars bo'lishi kerak")
        if not course.description:
            raise ValidationError("Kurs tavsifi to'ldirilishi kerak")
        if not course.cover_url:
            raise ValidationError("Muqova rasm yuklanishi kerak")

        missing_video = await self.db.scalar(
            select(func.count(Lesson.id))
            .outerjoin(VideoAsset, VideoAsset.lesson_id == Lesson.id)
            .where(
                Lesson.module_id.in_(module_ids),
                Lesson.content_type == LessonContentType.video,
                Lesson.is_published.is_(True),
                VideoAsset.id.is_(None),
            )
        )
        if missing_video:
            raise ValidationError(
                f"{missing_video} ta video darsga video yuklanmagan — moderatsiyaga yuborilmadi"
            )

    async def moderate(
        self,
        admin: User,
        course_id: uuid.UUID,
        action: ModerationAction,
        comment: str | None = None,
    ) -> Course:
        if admin.role is not UserRole.admin:
            raise PermissionDeniedError("Faqat super-admin moderatsiya qila oladi")

        course = await self.db.scalar(select(Course).where(Course.id == course_id))
        if course is None:
            raise NotFoundError("Kurs topilmadi")

        previous = course.status
        if action is ModerationAction.approve:
            course.status = CourseStatus.published
            course.published_at = course.published_at or datetime.now(UTC)
            course.rejection_reason = None
        elif action is ModerationAction.reject:
            course.status = CourseStatus.rejected
            course.rejection_reason = comment
        elif action is ModerationAction.archive:
            course.status = CourseStatus.archived
        else:
            raise ValidationError("Noto'g'ri moderatsiya amali")

        self.db.add(
            ModerationLog(
                course_id=course.id,
                actor_id=admin.id,
                action=action,
                from_status=previous.value,
                to_status=course.status.value,
                comment=comment,
            )
        )
        await self.db.commit()
        await self.db.refresh(course, ["owner", "category"])
        logger.info("Moderatsiya: %s → %s (%s)", previous, course.status, course.id)
        return course

    async def pending_courses(self, pagination: Pagination) -> tuple[list[Course], int]:
        stmt = (
            select(Course)
            .where(Course.status == CourseStatus.pending)
            .options(selectinload(Course.owner), selectinload(Course.category))
        )
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = await self.db.scalars(
            stmt.order_by(Course.submitted_at.asc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows.all()), int(total)


class ReviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add_review(
        self, user: User, course_id: uuid.UUID, rating: int, comment: str | None
    ) -> CourseReview:
        enrollment = await self.db.scalar(
            select(Enrollment).where(
                Enrollment.user_id == user.id, Enrollment.course_id == course_id
            )
        )
        if enrollment is None:
            raise PermissionDeniedError("Sharh yozish uchun kursga yozilgan bo'lishingiz kerak")

        existing = await self.db.scalar(
            select(CourseReview).where(
                CourseReview.course_id == course_id, CourseReview.user_id == user.id
            )
        )
        if existing:
            existing.rating = rating
            existing.comment = comment
            review = existing
        else:
            review = CourseReview(
                course_id=course_id, user_id=user.id, rating=rating, comment=comment
            )
            self.db.add(review)

        await self.db.commit()
        await self.recalculate_rating(course_id)
        await self.db.refresh(review, ["user"])
        return review

    async def recalculate_rating(self, course_id: uuid.UUID) -> None:
        stats = (
            await self.db.execute(
                select(func.avg(CourseReview.rating), func.count(CourseReview.id)).where(
                    CourseReview.course_id == course_id,
                    CourseReview.status == ReviewStatus.approved,
                )
            )
        ).one()
        course = await self.db.scalar(select(Course).where(Course.id == course_id))
        if course is None:
            return
        course.rating_avg = round(float(stats[0] or 0), 2)
        course.rating_count = int(stats[1] or 0)
        await self.db.commit()

    async def list_reviews(
        self, course_id: uuid.UUID, pagination: Pagination
    ) -> tuple[list[CourseReview], int]:
        stmt = (
            select(CourseReview)
            .where(
                CourseReview.course_id == course_id,
                CourseReview.status == ReviewStatus.approved,
            )
            .options(selectinload(CourseReview.user))
        )
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = await self.db.scalars(
            stmt.order_by(CourseReview.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows.all()), int(total)


async def quiz_exists(db: AsyncSession, lesson_id: uuid.UUID) -> bool:
    return await db.scalar(select(Quiz.id).where(Quiz.lesson_id == lesson_id)) is not None
