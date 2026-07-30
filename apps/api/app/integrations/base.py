from __future__ import annotations

import abc
import logging
from typing import Any

import httpx

from app.core.exceptions import IntegrationError
from app.models.enums import IntegrationKind

logger = logging.getLogger(__name__)


class IntegrationAdapter(abc.ABC):
    kind: IntegrationKind
    provider_name: str
    display_name: str

    def is_configured(self) -> bool:
        return True

    async def healthcheck(self) -> tuple[bool, str | None]:
        return self.is_configured(), None if self.is_configured() else "Sozlanmagan"

    async def _request(
        self,
        method: str,
        url: str,
        *,
        timeout: float = 20.0,
        **kwargs: Any,
    ) -> httpx.Response:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            logger.error("[%s] HTTP xatolik: %s", self.provider_name, exc)
            raise IntegrationError(
                f"{self.display_name} bilan bog'lanib bo'lmadi: {exc}",
                provider=self.provider_name,
            ) from exc

        if response.status_code >= 400:
            logger.error(
                "[%s] %s %s → %s: %s",
                self.provider_name,
                method,
                url,
                response.status_code,
                response.text[:500],
            )
            raise IntegrationError(
                f"{self.display_name} xatolik qaytardi ({response.status_code})",
                provider=self.provider_name,
                details=response.text[:500],
            )
        return response
