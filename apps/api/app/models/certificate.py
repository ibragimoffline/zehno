from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JSONType, UUIDType

if TYPE_CHECKING:
    from app.models.learning import Enrollment


class Certificate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "certificates"

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("enrollments.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    certificate_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    pdf_url: Mapped[str | None] = mapped_column(String(1024))
    pdf_object_key: Mapped[str | None] = mapped_column(String(512))
    verification_url: Mapped[str | None] = mapped_column(String(512))

    snapshot: Mapped[dict | None] = mapped_column(JSONType)

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    enrollment: Mapped[Enrollment] = relationship(back_populates="certificate")

    @property
    def is_valid(self) -> bool:
        return self.revoked_at is None
