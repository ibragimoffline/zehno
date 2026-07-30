from __future__ import annotations

import abc
from dataclasses import dataclass, field

from app.integrations.base import IntegrationAdapter
from app.models.enums import IntegrationKind, NotificationChannel


@dataclass(slots=True)
class NotificationMessage:
    recipient: str
    body: str
    subject: str | None = None
    parse_mode: str | None = "HTML"
    buttons: list[dict] = field(default_factory=list)
    disable_notification: bool = False


class NotificationProvider(IntegrationAdapter, abc.ABC):
    kind = IntegrationKind.notification
    channel: NotificationChannel

    @abc.abstractmethod
    async def send(self, message: NotificationMessage) -> bool: ...
