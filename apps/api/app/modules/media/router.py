"""Video yuklash (teacher) va himoyalangan playback (talaba) endpointlari.

Video ruxsati: playback URL faqat kursga yozilgan foydalanuvchiga (yoki dars
`is_preview=True` bo'lsa hammaga) beriladi va 10-15 daqiqada tugaydi
(`ARCHITECTURE.md` 6.1, 10-bo'lim).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, File, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, OptionalUser, TeacherUser
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.integrations.factory import get_video_provider
from app.integrations.storage.s3 import StorageService
from app.integrations.video.base import VideoMeta
from app.models.catalog import Lesson, VideoAsset
from app.models.enums import LessonContentType, VideoAssetStatus
from app.models.learning import Enrollment
from app.modules.courses.schemas import VideoAssetPublic
from app.modules.courses.service import CourseAuthoringService
from app.schemas.common import Message

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Media"])

MAX_VIDEO_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB
MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB (PDF/rasm)
ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
    "video/x-msvideo",
    "application/octet-stream",
}
ALLOWED_FILE_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/zip",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class PlaybackResponse(BaseModel):
    url: str
    expires_at: datetime
    content_type: str
    provider: str
    thumbnail_url: str | None = None


class UploadedFileResponse(BaseModel):
    url: str
    object_key: str
    filename: str
    size_bytes: int
    content_type: str


# ===================================================================
#  Teacher: video yuklash
# ===================================================================
@router.post(
    "/lessons/{lesson_id}/video",
    response_model=VideoAssetPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Darsga video yuklash (provayderga proxy)",
)
async def upload_lesson_video(
    lesson_id: uuid.UUID,
    user: TeacherUser,
    db: DbSession,
    file: UploadFile = File(..., description="Video fayl (max 2 GB)"),
) -> VideoAssetPublic:
    service = CourseAuthoringService(db)
    lesson = await service.get_lesson_for_edit(user, lesson_id)

    if file.content_type and file.content_type not in ALLOWED_VIDEO_TYPES:
        raise ValidationError(f"Video formati qo'llab-quvvatlanmaydi: {file.content_type}")

    payload = await file.read()
    if not payload:
        raise ValidationError("Fayl bo'sh")
    if len(payload) > MAX_VIDEO_BYTES:
        raise ValidationError("Video hajmi 2 GB dan oshmasligi kerak")

    provider = get_video_provider()
    result = await provider.upload_video(
        payload,
        VideoMeta(
            title=lesson.title,
            description=lesson.description,
            lesson_id=str(lesson.id),
            course_id=str(lesson.module.course_id),
            filename=file.filename,
            content_type=file.content_type,
            private=True,
        ),
    )

    asset = lesson.video_asset
    if asset is None:
        asset = VideoAsset(
            lesson_id=lesson.id, provider=provider.provider_name, external_video_id=""
        )
        db.add(asset)

    asset.provider = provider.provider_name
    asset.external_video_id = result.video_id
    asset.status = result.status
    asset.duration_seconds = result.duration_seconds or asset.duration_seconds
    asset.thumbnail_url = result.thumbnail_url
    asset.original_filename = file.filename
    asset.size_bytes = len(payload)
    asset.provider_meta = result.provider_meta
    asset.error_message = None

    if lesson.content_type is not LessonContentType.video:
        lesson.content_type = LessonContentType.video

    await db.commit()
    await db.refresh(asset)

    # Transkodlash holatini fon rejimida kuzatamiz
    if asset.status is VideoAssetStatus.processing:
        from app.worker.tasks.video import poll_video_status

        poll_video_status.apply_async(args=[str(asset.id)], countdown=30)

    logger.info("Video yuklandi: lesson=%s provider=%s", lesson.id, provider.provider_name)
    return VideoAssetPublic.model_validate(asset)


@router.get(
    "/lessons/{lesson_id}/video/status",
    response_model=VideoAssetPublic,
    summary="Video transkodlash holati",
)
async def video_status(lesson_id: uuid.UUID, user: TeacherUser, db: DbSession) -> VideoAssetPublic:
    lesson = await CourseAuthoringService(db).get_lesson_for_edit(user, lesson_id)
    if lesson.video_asset is None:
        raise NotFoundError("Bu darsga video yuklanmagan")

    asset = lesson.video_asset
    if asset.status is VideoAssetStatus.processing:
        provider = get_video_provider(asset.provider)
        asset.status = await provider.get_upload_status(asset.external_video_id)
        await db.commit()
        await db.refresh(asset)
    return VideoAssetPublic.model_validate(asset)


@router.delete(
    "/lessons/{lesson_id}/video", response_model=Message, summary="Darsdagi videoni o'chirish"
)
async def delete_lesson_video(lesson_id: uuid.UUID, user: TeacherUser, db: DbSession) -> Message:
    lesson = await CourseAuthoringService(db).get_lesson_for_edit(user, lesson_id)
    if lesson.video_asset is None:
        raise NotFoundError("Bu darsga video yuklanmagan")

    asset = lesson.video_asset
    try:
        await get_video_provider(asset.provider).delete_video(asset.external_video_id)
    except Exception as exc:  # provayderdagi xato DB'ni bloklamasligi kerak
        logger.warning("Video provayderdan o'chirilmadi: %s", exc)

    await db.delete(asset)
    await db.commit()
    return Message(message="Video o'chirildi")


# ===================================================================
#  Talaba: himoyalangan playback
# ===================================================================
@router.get(
    "/lessons/{lesson_id}/playback",
    response_model=PlaybackResponse,
    summary="Vaqtinchalik video havolasi (signed URL)",
)
async def get_playback_url(
    lesson_id: uuid.UUID,
    user: OptionalUser,
    db: DbSession,
) -> PlaybackResponse:
    lesson = await db.scalar(select(Lesson).where(Lesson.id == lesson_id))
    if lesson is None:
        raise NotFoundError("Dars topilmadi")

    asset = await db.scalar(select(VideoAsset).where(VideoAsset.lesson_id == lesson.id))
    if asset is None:
        raise NotFoundError("Bu darsda video yo'q")
    if asset.status is not VideoAssetStatus.ready:
        raise ValidationError("Video hali tayyor emas (transkodlanmoqda)")

    # Preview darslar hammaga ochiq; qolganlari uchun enrollment tekshiriladi
    if not lesson.is_preview:
        if user is None:
            raise PermissionDeniedError("Videoni ko'rish uchun tizimga kiring")
        await _assert_has_access(db, user.id, lesson)

    provider = get_video_provider(asset.provider)
    playback = await provider.get_playback_url(
        asset.external_video_id, str(user.id) if user else "anonymous"
    )
    return PlaybackResponse(
        url=playback.url,
        expires_at=playback.expires_at,
        content_type=playback.content_type,
        provider=asset.provider,
        thumbnail_url=playback.thumbnail_url or asset.thumbnail_url,
    )


@router.get(
    "/lessons/{lesson_id}/embed",
    response_model=dict,
    summary="Embed kod (iframe)",
)
async def get_embed(lesson_id: uuid.UUID, user: CurrentUser, db: DbSession) -> dict:
    lesson = await db.scalar(select(Lesson).where(Lesson.id == lesson_id))
    if lesson is None:
        raise NotFoundError("Dars topilmadi")
    asset = await db.scalar(select(VideoAsset).where(VideoAsset.lesson_id == lesson.id))
    if asset is None:
        raise NotFoundError("Bu darsda video yo'q")
    if not lesson.is_preview:
        await _assert_has_access(db, user.id, lesson)

    provider = get_video_provider(asset.provider)
    return {"embed": await provider.get_embed_code(asset.external_video_id)}


async def _assert_has_access(db, user_id: uuid.UUID, lesson: Lesson) -> None:
    from app.models.catalog import CourseModule

    course_id = await db.scalar(
        select(CourseModule.course_id).where(CourseModule.id == lesson.module_id)
    )
    enrollment = await db.scalar(
        select(Enrollment.id).where(
            Enrollment.user_id == user_id, Enrollment.course_id == course_id
        )
    )
    if enrollment is None:
        # Kurs egasi va admin ham ko'ra oladi
        from app.models.catalog import Course
        from app.models.enums import UserRole
        from app.models.user import User

        user = await db.scalar(select(User).where(User.id == user_id))
        course = await db.scalar(select(Course).where(Course.id == course_id))
        if user and course and (user.role is UserRole.admin or course.owner_id == user.id):
            return
        raise PermissionDeniedError("Bu kursni sotib olmagansiz")


# ===================================================================
#  Umumiy fayl yuklash (muqova rasm, PDF material)
# ===================================================================
@router.post(
    "/uploads",
    response_model=UploadedFileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Rasm/PDF yuklash (muqova, materiallar)",
)
async def upload_file(
    user: CurrentUser,
    file: UploadFile = File(...),
    folder: str = Query(default="uploads", pattern="^[a-z0-9_-]{2,32}$"),
) -> UploadedFileResponse:
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise ValidationError(f"Fayl turi qo'llab-quvvatlanmaydi: {file.content_type}")

    payload = await file.read()
    if len(payload) > MAX_FILE_BYTES:
        raise ValidationError("Fayl hajmi 50 MB dan oshmasligi kerak")

    import asyncio

    storage = StorageService()
    safe_name = (file.filename or "file").replace("/", "_").replace("\\", "_")[:120]
    key = f"public/{folder}/{user.id}/{uuid.uuid4().hex[:10]}-{safe_name}"
    await asyncio.to_thread(
        storage.put_object,
        key,
        payload,
        content_type=file.content_type or "application/octet-stream",
    )

    return UploadedFileResponse(
        url=storage.public_url(key),
        object_key=key,
        filename=safe_name,
        size_bytes=len(payload),
        content_type=file.content_type or "application/octet-stream",
    )
