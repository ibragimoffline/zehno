"""PeerTube provayderi — MVP uchun asosiy tanlov (bepul, self-hosted, HLS).

Oqim:
1. `/api/v1/oauth-clients/local` → client_id/client_secret
2. `/api/v1/users/token` → access_token (parol grant)
3. `/api/v1/videos/upload` → video yuklash (privacy=private)
4. `/api/v1/videos/{id}/token` → 10 daqiqalik video file token (signed playback)

Videolar `private` sifatida yuklanadi — faqat token bilan ko'rish mumkin, ya'ni
havola tarqatilsa ham bir necha daqiqadan keyin ishlamaydi.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.exceptions import IntegrationError
from app.integrations.video.base import PlaybackUrl, UploadResult, VideoMeta, VideoProvider
from app.models.enums import VideoAssetStatus

logger = logging.getLogger(__name__)

# PeerTube privacy kodlari
PRIVACY_PUBLIC = 1
PRIVACY_UNLISTED = 2
PRIVACY_PRIVATE = 3
PRIVACY_INTERNAL = 4

# PeerTube video state kodlari
STATE_PUBLISHED = 1
STATE_TO_TRANSCODE = 2
STATE_TO_IMPORT = 3
STATE_WAITING_FOR_LIVE = 4
STATE_LIVE_ENDED = 5
STATE_TO_MOVE_TO_EXTERNAL_STORAGE = 6
STATE_TRANSCODING_FAILED = 7


class PeerTubeProvider(VideoProvider):
    provider_name = "peertube"
    display_name = "PeerTube"

    def __init__(self) -> None:
        self.base_url = settings.PEERTUBE_BASE_URL.rstrip("/")
        self._token: str | None = None
        self._token_expires: datetime | None = None

    def is_configured(self) -> bool:
        return bool(
            settings.PEERTUBE_BASE_URL and settings.PEERTUBE_USERNAME and settings.PEERTUBE_PASSWORD
        )

    # ------------------------------------------------------------ auth
    async def _access_token(self) -> str:
        if self._token and self._token_expires and self._token_expires > datetime.now(UTC):
            return self._token

        if not self.is_configured():
            raise IntegrationError(
                "PeerTube sozlanmagan (PEERTUBE_USERNAME / PEERTUBE_PASSWORD)",
                provider=self.provider_name,
            )

        clients = (await self._request("GET", f"{self.base_url}/api/v1/oauth-clients/local")).json()
        response = await self._request(
            "POST",
            f"{self.base_url}/api/v1/users/token",
            data={
                "client_id": clients["client_id"],
                "client_secret": clients["client_secret"],
                "grant_type": "password",
                "response_type": "code",
                "username": settings.PEERTUBE_USERNAME,
                "password": settings.PEERTUBE_PASSWORD,
            },
        )
        payload = response.json()
        self._token = payload["access_token"]
        self._token_expires = datetime.now(UTC) + timedelta(
            seconds=int(payload.get("expires_in", 3600)) - 60
        )
        return self._token

    async def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {await self._access_token()}"}

    # ------------------------------------------------------------ interfeys
    async def upload_video(self, file_bytes: bytes, meta: VideoMeta) -> UploadResult:
        channel_id = settings.PEERTUBE_CHANNEL_ID
        if not channel_id:
            # Foydalanuvchining birinchi kanalini avtomatik aniqlaymiz
            me = (
                await self._request(
                    "GET",
                    f"{self.base_url}/api/v1/users/me",
                    headers=await self._auth_headers(),
                )
            ).json()
            channels = me.get("videoChannels") or []
            if not channels:
                raise IntegrationError(
                    "PeerTube foydalanuvchisida video kanal topilmadi",
                    provider=self.provider_name,
                )
            channel_id = str(channels[0]["id"])

        form = {
            "name": meta.title[:120],
            "channelId": channel_id,
            "privacy": str(PRIVACY_PRIVATE if meta.private else PRIVACY_UNLISTED),
            "waitTranscoding": "false",
        }
        if meta.description:
            form["description"] = meta.description[:1000]

        response = await self._request(
            "POST",
            f"{self.base_url}/api/v1/videos/upload",
            headers=await self._auth_headers(),
            data=form,
            files={
                "videofile": (
                    meta.filename or "video.mp4",
                    file_bytes,
                    meta.content_type or "video/mp4",
                )
            },
            timeout=600.0,
        )
        video = response.json().get("video", {})
        return UploadResult(
            video_id=str(video.get("uuid") or video.get("id")),
            status=VideoAssetStatus.processing,
            provider_meta={"short_uuid": video.get("shortUUID"), "id": video.get("id")},
        )

    async def get_playback_url(self, video_id: str, user_id: str) -> PlaybackUrl:
        headers = await self._auth_headers()

        # 10 daqiqalik video file token (PeerTube 5+)
        token_response = await self._request(
            "POST", f"{self.base_url}/api/v1/videos/{video_id}/token", headers=headers
        )
        file_token = token_response.json().get("files", {}).get("token")

        video = (
            await self._request("GET", f"{self.base_url}/api/v1/videos/{video_id}", headers=headers)
        ).json()

        streaming = video.get("streamingPlaylists") or []
        if streaming:
            url = streaming[0]["playlistUrl"]
            content_type = "application/x-mpegURL"
        else:
            files = video.get("files") or []
            if not files:
                raise IntegrationError("Video hali transkodlanmagan", provider=self.provider_name)
            url = files[-1]["fileUrl"]
            content_type = "video/mp4"

        if file_token:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}videoFileToken={file_token}"

        return PlaybackUrl(
            url=url,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
            content_type=content_type,
            thumbnail_url=(
                f"{self.base_url}{video['thumbnailPath']}" if video.get("thumbnailPath") else None
            ),
        )

    async def get_embed_code(self, video_id: str) -> str:
        return (
            f'<iframe src="{self.base_url}/videos/embed/{video_id}" '
            'style="width:100%;aspect-ratio:16/9;border:0" allowfullscreen '
            'sandbox="allow-same-origin allow-scripts allow-popups"></iframe>'
        )

    async def delete_video(self, video_id: str) -> None:
        await self._request(
            "DELETE",
            f"{self.base_url}/api/v1/videos/{video_id}",
            headers=await self._auth_headers(),
        )

    async def get_upload_status(self, video_id: str) -> VideoAssetStatus:
        video = (
            await self._request(
                "GET",
                f"{self.base_url}/api/v1/videos/{video_id}",
                headers=await self._auth_headers(),
            )
        ).json()
        state = (video.get("state") or {}).get("id")
        if state == STATE_PUBLISHED:
            return VideoAssetStatus.ready
        if state == STATE_TRANSCODING_FAILED:
            return VideoAssetStatus.failed
        return VideoAssetStatus.processing

    async def healthcheck(self) -> tuple[bool, str | None]:
        if not self.is_configured():
            return False, "PeerTube sozlanmagan"
        try:
            await self._request("GET", f"{self.base_url}/api/v1/config")
            return True, None
        except IntegrationError as exc:
            return False, str(exc)
