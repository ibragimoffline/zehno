from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.integrations.storage.s3 import StorageService
from app.integrations.video.base import PlaybackUrl, UploadResult, VideoMeta, VideoProvider
from app.models.enums import VideoAssetStatus

logger = logging.getLogger(__name__)


class MockVideoProvider(VideoProvider):
    provider_name = "mock"
    display_name = "Mock Video (S3)"

    def __init__(self) -> None:
        self.storage = StorageService()

    def is_configured(self) -> bool:
        return True

    async def upload_video(self, file_bytes: bytes, meta: VideoMeta) -> UploadResult:
        video_id = uuid.uuid4().hex
        key = f"videos/{video_id}/{meta.filename or 'video.mp4'}"
        await asyncio.to_thread(
            self.storage.put_object, key, file_bytes, content_type=meta.content_type or "video/mp4"
        )
        logger.info("[mock] video yuklandi: %s (%s bayt)", key, len(file_bytes))
        return UploadResult(
            video_id=video_id,
            status=VideoAssetStatus.ready,
            provider_meta={"object_key": key, "size": len(file_bytes)},
        )

    async def get_playback_url(self, video_id: str, user_id: str) -> PlaybackUrl:
        key = await asyncio.to_thread(self.storage.find_first, f"videos/{video_id}/")
        if key is None:
            return PlaybackUrl(
                url="https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
                expires_at=datetime.now(UTC)
                + timedelta(minutes=settings.VIDEO_SIGNED_URL_TTL_MINUTES),
            )
        ttl = settings.VIDEO_SIGNED_URL_TTL_MINUTES * 60
        return PlaybackUrl(
            url=await asyncio.to_thread(self.storage.presigned_url, key, ttl),
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl),
            content_type="video/mp4",
        )

    async def get_embed_code(self, video_id: str) -> str:
        return (
            f'<video controls playsinline style="width:100%" '
            f'src="{settings.PUBLIC_API_URL}/api/v1/lessons/video/{video_id}"></video>'
        )

    async def delete_video(self, video_id: str) -> None:
        await asyncio.to_thread(self.storage.delete_prefix, f"videos/{video_id}/")

    async def get_upload_status(self, video_id: str) -> VideoAssetStatus:
        return VideoAssetStatus.ready
