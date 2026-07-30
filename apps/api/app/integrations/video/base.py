"""VideoProvider interfeysi.

`ARCHITECTURE.md` 6.1 dagi TypeScript interfeysining Python ekvivalenti:

```typescript
export interface VideoProvider {
  uploadVideo(file, meta): Promise<{videoId, status}>;
  getPlaybackUrl(videoId, userId): Promise<{url, expiresAt}>;
  getEmbedCode(videoId): Promise<string>;
  deleteVideo(videoId): Promise<void>;
  getUploadStatus(videoId): Promise<'processing'|'ready'|'failed'>;
}
```
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime

from app.integrations.base import IntegrationAdapter
from app.models.enums import IntegrationKind, VideoAssetStatus


@dataclass(slots=True)
class VideoMeta:
    title: str
    description: str | None = None
    lesson_id: str | None = None
    course_id: str | None = None
    filename: str | None = None
    content_type: str | None = None
    private: bool = True
    extra: dict = field(default_factory=dict)


@dataclass(slots=True)
class UploadResult:
    video_id: str
    status: VideoAssetStatus
    duration_seconds: int = 0
    thumbnail_url: str | None = None
    provider_meta: dict = field(default_factory=dict)


@dataclass(slots=True)
class PlaybackUrl:
    url: str
    expires_at: datetime
    #: HLS manifest bo'lsa `application/x-mpegURL`, mp4 bo'lsa `video/mp4`
    content_type: str = "application/x-mpegURL"
    thumbnail_url: str | None = None


class VideoProvider(IntegrationAdapter, abc.ABC):
    kind = IntegrationKind.video

    @abc.abstractmethod
    async def upload_video(self, file_bytes: bytes, meta: VideoMeta) -> UploadResult:
        """Videoni provayderga yuklaydi."""

    @abc.abstractmethod
    async def get_playback_url(self, video_id: str, user_id: str) -> PlaybackUrl:
        """Vaqtinchalik (signed) playback URL qaytaradi — 10-15 daqiqa amal qiladi."""

    @abc.abstractmethod
    async def get_embed_code(self, video_id: str) -> str:
        """`<iframe>` embed kodi."""

    @abc.abstractmethod
    async def delete_video(self, video_id: str) -> None:
        """Videoni provayderdan o'chiradi."""

    @abc.abstractmethod
    async def get_upload_status(self, video_id: str) -> VideoAssetStatus:
        """Transkodlash holati."""
