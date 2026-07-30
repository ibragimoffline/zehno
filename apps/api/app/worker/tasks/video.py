"""Video transkodlash holatini kuzatish task'lari."""

from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import sync_session
from app.integrations.factory import get_video_provider
from app.models.catalog import CourseModule, Lesson, VideoAsset
from app.models.enums import VideoAssetStatus
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

MAX_POLLS = 60  # ~30 daqiqa (30 sekundlik intervalda)


@celery_app.task(name="app.worker.tasks.video.poll_video_status", bind=True)
def poll_video_status(self, video_asset_id: str, attempt: int = 1) -> dict:
    """Provayderdan transkodlash holatini so'raydi, tayyor bo'lguncha qayta rejalashtiradi."""
    with sync_session() as db:
        asset = db.scalar(
            select(VideoAsset)
            .where(VideoAsset.id == uuid.UUID(video_asset_id))
            .options(selectinload(VideoAsset.lesson))
        )
        if asset is None:
            return {"skipped": "video asset topilmadi"}
        if asset.status is not VideoAssetStatus.processing:
            return {"status": asset.status.value, "done": True}

        provider = get_video_provider(asset.provider)
        try:
            status = asyncio.run(provider.get_upload_status(asset.external_video_id))
        except Exception as exc:
            logger.warning("Video holatini olishda xato: %s", exc)
            if attempt < MAX_POLLS:
                poll_video_status.apply_async(args=[video_asset_id, attempt + 1], countdown=60)
            return {"error": str(exc), "attempt": attempt}

        asset.status = status
        if status is VideoAssetStatus.failed:
            asset.error_message = "Provayder transkodlashda xato qaytardi"
        db.commit()

        if status is VideoAssetStatus.ready:
            recalculate_lesson_duration.delay(str(asset.lesson_id))
            return {"status": "ready", "attempts": attempt}

        if status is VideoAssetStatus.processing and attempt < MAX_POLLS:
            poll_video_status.apply_async(args=[video_asset_id, attempt + 1], countdown=30)

        return {"status": status.value, "attempts": attempt}


@celery_app.task(name="app.worker.tasks.video.recalculate_lesson_duration")
def recalculate_lesson_duration(lesson_id: str) -> dict:
    """Video tayyor bo'lgach dars va kurs davomiyligini yangilaydi."""
    from sqlalchemy import func

    from app.models.catalog import Course

    with sync_session() as db:
        lesson = db.scalar(
            select(Lesson)
            .where(Lesson.id == uuid.UUID(lesson_id))
            .options(selectinload(Lesson.video_asset))
        )
        if lesson is None:
            return {"skipped": "dars topilmadi"}

        if lesson.video_asset and lesson.video_asset.duration_seconds:
            lesson.duration_seconds = lesson.video_asset.duration_seconds

        course_id = db.scalar(
            select(CourseModule.course_id).where(CourseModule.id == lesson.module_id)
        )
        if course_id:
            totals = db.execute(
                select(
                    func.count(Lesson.id),
                    func.coalesce(func.sum(Lesson.duration_seconds), 0),
                )
                .select_from(Lesson)
                .join(CourseModule, Lesson.module_id == CourseModule.id)
                .where(CourseModule.course_id == course_id, Lesson.is_published.is_(True))
            ).one()

            course = db.scalar(select(Course).where(Course.id == course_id))
            if course:
                course.lessons_count = int(totals[0] or 0)
                course.duration_seconds = int(totals[1] or 0)

        db.commit()
        return {"lesson_id": lesson_id, "duration": lesson.duration_seconds}


@celery_app.task(name="app.worker.tasks.video.delete_remote_video")
def delete_remote_video(provider_name: str, external_video_id: str) -> dict:
    """Kurs o'chirilganda provayderdagi videolarni tozalash."""
    provider = get_video_provider(provider_name)
    try:
        asyncio.run(provider.delete_video(external_video_id))
        return {"deleted": external_video_id}
    except Exception as exc:
        logger.warning("Video o'chirilmadi (%s): %s", external_video_id, exc)
        return {"error": str(exc)}
