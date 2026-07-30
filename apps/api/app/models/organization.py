from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JSONType, UUIDType
from app.models.enums import OrganizationType

if TYPE_CHECKING:
    from app.models.catalog import Course
    from app.models.crm import CrmSyncLog
    from app.models.user import User


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType, native_enum=False, length=20, validate_strings=True),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(512))
    website: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(32))

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_organizations_owner_id_users",
        ),
        index=True,
    )

    commission_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))

    seats_purchased: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    crm_provider: Mapped[str | None] = mapped_column(String(32))
    crm_external_id: Mapped[str | None] = mapped_column(String(128), index=True)
    crm_company_id: Mapped[str | None] = mapped_column(String(128))
    crm_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    payout_details: Mapped[dict | None] = mapped_column(JSONType)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    members: Mapped[list[User]] = relationship(
        back_populates="organization", foreign_keys="User.organization_id"
    )
    courses: Mapped[list[Course]] = relationship(back_populates="organization")
    crm_sync_logs: Mapped[list[CrmSyncLog]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )

    @property
    def seats_label(self) -> str:
        return f"{self.seats_purchased} o'rin"
