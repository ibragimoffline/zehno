from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JSONType, UUIDType
from app.models.enums import CrmSyncStatus

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class CrmSyncLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "crm_sync_log"
    __table_args__ = (Index("ix_crm_sync_org_created", "organization_id", "created_at"),)

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL")
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(16), default="outbound", nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONType)
    response: Mapped[dict | None] = mapped_column(JSONType)
    external_id: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[CrmSyncStatus] = mapped_column(
        Enum(CrmSyncStatus, native_enum=False, length=20, validate_strings=True),
        default=CrmSyncStatus.pending,
        nullable=False,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    organization: Mapped[Organization | None] = relationship(back_populates="crm_sync_logs")
    user: Mapped[User | None] = relationship()
