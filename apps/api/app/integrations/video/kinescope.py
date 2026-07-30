from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.exceptions import IntegrationError
from app.integrations.video.base import PlaybackUrl, UploadResult, VideoMeta, VideoProvider
from app.models.enums import VideoAssetStatus

logger = logging.getLogger(__name__)

API_BASE = "https://api.kinescope.io/v1"
UPLOAD_BASE = "https://uploader.kinescope.io/v2"

STATUS_MAP = {
    "uploading": VideoAssetStatus.processing,
    "processing": VideoAssetStatus.processing,
    "pending": VideoAssetStatus.processing,
    "done": VideoAssetStatus.ready,
    "ready": VideoAssetStatus.ready,
    "error": VideoAssetStatus.failed,
    "failed": VideoAssetStatus.failed,
}


class KinescopeProvider(VideoProvider):
    provider_name = "kinescope"
    display_name = "Kinescope"

    def is_configured(self) -> bool:
        return bool(settings.KINESCOPE_API_KEY and settings.KINESCOPE_PROJECT_ID)

    def _headers(self) -> dict[str, str]:
        if not self.is_configured():
            raise IntegrationError(
                "Kinescope sozlanmagan (KINESCOPE_API_KEY / KINESCOPE_PROJECT_ID)",
                provider=self.provider_name,
            )
        return {"Authorization": f"Bearer {settings.KINESCOPE_API_KEY}"}

    async def upload_video(self, file_bytes: bytes, meta: VideoMeta) -> UploadResult:
        headers = {
            **self._headers(),
            "X-Video-Title": meta.title[:120],
            "X-Parent-ID": settings.KINESCOPE_PROJECT_ID or "",
            "X-File-Name": meta.filename or "video.mp4",
            "Content-Type": meta.content_type or "video/mp4",
        }
        response = await self._request(
            "POST", f"{UPLOAD_BASE}/video", headers=headers, content=file_bytes, timeout=600.0
        )
        data = response.json().get("data", {})
        return UploadResult(
            video_id=str(data.get("id")),
            status=STATUS_MAP.get(str(data.get("status", "")).lower(), VideoAssetStatus.processing),
            provider_meta={"project_id": settings.KINESCOPE_PROJECT_ID},
        )

    async def get_playback_url(self, video_id: str, user_id: str) -> PlaybackUrl:
        response = await self._request(
            "GET", f"{API_BASE}/videos/{video_id}", headers=self._headers()
        )
        data = response.json().get("data", {})
        url = data.get("hls_link") or data.get("play_link")
        if not url:
            raise IntegrationError("Kinescope playback havolasi topilmadi", provider="kinescope")
        return PlaybackUrl(
            url=url,
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.VIDEO_SIGNED_URL_TTL_MINUTES),
            thumbnail_url=data.get("poster", {}).get("original")
            if isinstance(data.get("poster"), dict)
            else data.get("poster"),
        )

    async def get_embed_code(self, video_id: str) -> str:
        return (
            f'<iframe src="https://kinescope.io/embed/{video_id}" '
            'style="width:100%;aspect-ratio:16/9;border:0" allowfullscreen></iframe>'
        )

    async def delete_video(self, video_id: str) -> None:
        await self._request("DELETE", f"{API_BASE}/videos/{video_id}", headers=self._headers())

    async def get_upload_status(self, video_id: str) -> VideoAssetStatus:
        response = await self._request(
            "GET", f"{API_BASE}/videos/{video_id}", headers=self._headers()
        )
        status = str(response.json().get("data", {}).get("status", "")).lower()
        return STATUS_MAP.get(status, VideoAssetStatus.processing)

    async def healthcheck(self) -> tuple[bool, str | None]:
        if not self.is_configured():
            return False, "Kinescope sozlanmagan"
        try:
            await self._request("GET", f"{API_BASE}/projects", headers=self._headers())
            return True, None
        except IntegrationError as exc:
            return False, str(exc)
