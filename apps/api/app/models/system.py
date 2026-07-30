from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JSONType, UUIDType
from app.models.enums import (
    IntegrationHealth,
    IntegrationKind,
    NotificationChannel,
    NotificationStatus,
)

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_actor_created", "actor_id", "created_at"),)

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL")
    )
    actor_email: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(60))
    entity_id: Mapped[str | None] = mapped_column(String(60))
    changes: Mapped[dict | None] = mapped_column(JSONType)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))

    actor: Mapped[User | None] = relationship()


class NotificationLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notification_logs"
    __table_args__ = (Index("ix_notification_user_created", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, native_enum=False, length=20, validate_strings=True),
        nullable=False,
    )
    template: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    recipient: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    context: Mapped[dict | None] = mapped_column(JSONType)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, native_enum=False, length=20, validate_strings=True),
        default=NotificationStatus.pending,
        nullable=False,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User | None] = relationship()


class IntegrationStatus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "integration_statuses"
    __table_args__ = (UniqueConstraint("kind", "provider", name="uq_integration_kind_provider"),)

    kind: Mapped[IntegrationKind] = mapped_column(
        Enum(IntegrationKind, native_enum=False, length=20, validate_strings=True),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    health: Mapped[IntegrationHealth] = mapped_column(
        Enum(IntegrationHealth, native_enum=False, length=20, validate_strings=True),
        default=IntegrationHealth.disabled,
        nullable=False,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_message: Mapped[str | None] = mapped_column(Text)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSONType)


class SystemSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    value: Mapped[dict | None] = mapped_column(JSONType)
    description: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
