"""Bunny Stream provayderi — arzon ($0.005/GB), token auth va watermark bilan."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.exceptions import IntegrationError
from app.integrations.video.base import PlaybackUrl, UploadResult, VideoMeta, VideoProvider
from app.models.enums import VideoAssetStatus

logger = logging.getLogger(__name__)

API_BASE = "https://video.bunnycdn.com/library"

# Bunny video status: 0-4 processing, 3/4 = playable, 5 = failed
STATUS_MAP = {
    0: VideoAssetStatus.processing,
    1: VideoAssetStatus.processing,
    2: VideoAssetStatus.processing,
    3: VideoAssetStatus.ready,
    4: VideoAssetStatus.ready,
    5: VideoAssetStatus.failed,
}


class BunnyStreamProvider(VideoProvider):
    provider_name = "bunny"
    display_name = "Bunny Stream"

    def is_configured(self) -> bool:
        return bool(settings.BUNNY_STREAM_LIBRARY_ID and settings.BUNNY_STREAM_API_KEY)

    @property
    def _library(self) -> str:
        if not self.is_configured():
            raise IntegrationError("Bunny Stream sozlanmagan", provider=self.provider_name)
        return str(settings.BUNNY_STREAM_LIBRARY_ID)

    def _headers(self) -> dict[str, str]:
        return {"AccessKey": settings.BUNNY_STREAM_API_KEY or "", "accept": "application/json"}

    async def upload_video(self, file_bytes: bytes, meta: VideoMeta) -> UploadResult:
        created = (
            await self._request(
                "POST",
                f"{API_BASE}/{self._library}/videos",
                headers={**self._headers(), "content-type": "application/json"},
                json={"title": meta.title[:200]},
            )
        ).json()
        video_id = created["guid"]

        await self._request(
            "PUT",
            f"{API_BASE}/{self._library}/videos/{video_id}",
            headers=self._headers(),
            content=file_bytes,
            timeout=600.0,
        )
        return UploadResult(video_id=video_id, status=VideoAssetStatus.processing)

    async def get_playback_url(self, video_id: str, user_id: str) -> PlaybackUrl:
        cdn = settings.BUNNY_STREAM_CDN_HOSTNAME
        if not cdn:
            raise IntegrationError("BUNNY_STREAM_CDN_HOSTNAME sozlanmagan", provider="bunny")

        expires_at = datetime.now(UTC) + timedelta(minutes=settings.VIDEO_SIGNED_URL_TTL_MINUTES)
        path = f"/{video_id}/playlist.m3u8"
        url = f"https://{cdn}{path}"

        # Token authentication (agar token kaliti sozlangan bo'lsa)
        if settings.BUNNY_STREAM_TOKEN_KEY:
            expiry = int(expires_at.timestamp())
            raw = f"{settings.BUNNY_STREAM_TOKEN_KEY}{path}{expiry}"
            token = hashlib.sha256(raw.encode()).hexdigest()
            url = f"{url}?token={token}&expires={expiry}"

        return PlaybackUrl(url=url, expires_at=expires_at)

    async def get_embed_code(self, video_id: str) -> str:
        return (
            f'<iframe src="https://iframe.mediadelivery.net/embed/{self._library}/{video_id}" '
            'style="width:100%;aspect-ratio:16/9;border:0" allowfullscreen></iframe>'
        )

    async def delete_video(self, video_id: str) -> None:
        await self._request(
            "DELETE", f"{API_BASE}/{self._library}/videos/{video_id}", headers=self._headers()
        )

    async def get_upload_status(self, video_id: str) -> VideoAssetStatus:
        data = (
            await self._request(
                "GET", f"{API_BASE}/{self._library}/videos/{video_id}", headers=self._headers()
            )
        ).json()
        return STATUS_MAP.get(int(data.get("status", 0)), VideoAssetStatus.processing)

    async def healthcheck(self) -> tuple[bool, str | None]:
        if not self.is_configured():
            return False, "Bunny Stream sozlanmagan"
        try:
            await self._request(
                "GET",
                f"{API_BASE}/{self._library}/videos?page=1&itemsPerPage=1",
                headers=self._headers(),
            )
            return True, None
        except IntegrationError as exc:
            return False, str(exc)
