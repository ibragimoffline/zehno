from __future__ import annotations

import abc
from dataclasses import dataclass, field

from app.integrations.base import IntegrationAdapter
from app.models.enums import IntegrationKind


@dataclass(slots=True)
class CrmContact:
    full_name: str
    email: str | None = None
    phone: str | None = None
    external_id: str | None = None
    company_external_id: str | None = None
    custom_fields: dict = field(default_factory=dict)


@dataclass(slots=True)
class CrmCompany:
    name: str
    external_id: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    custom_fields: dict = field(default_factory=dict)


@dataclass(slots=True)
class CrmProgressUpdate:
    contact_external_id: str
    course_title: str
    progress_percent: int
    completed: bool = False
    certificate_code: str | None = None
    quiz_score: int | None = None
    comment: str | None = None


class CrmProvider(IntegrationAdapter, abc.ABC):
    kind = IntegrationKind.crm

    @abc.abstractmethod
    async def upsert_company(self, company: CrmCompany) -> str: ...

    @abc.abstractmethod
    async def upsert_contact(self, contact: CrmContact) -> str: ...

    @abc.abstractmethod
    async def push_progress(self, update: CrmProgressUpdate) -> bool: ...

    async def create_deal(self, title: str, amount: float, contact_external_id: str) -> str | None:
        return None
