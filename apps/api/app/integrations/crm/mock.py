from __future__ import annotations

import logging
import uuid

from app.integrations.crm.base import CrmCompany, CrmContact, CrmProgressUpdate, CrmProvider

logger = logging.getLogger(__name__)


class MockCrmProvider(CrmProvider):
    provider_name = "mock"
    display_name = "Ichki mini-CRM"

    async def upsert_company(self, company: CrmCompany) -> str:
        external_id = company.external_id or f"mock-co-{uuid.uuid4().hex[:8]}"
        logger.info("[mock-crm] company upsert: %s → %s", company.name, external_id)
        return external_id

    async def upsert_contact(self, contact: CrmContact) -> str:
        external_id = contact.external_id or f"mock-ct-{uuid.uuid4().hex[:8]}"
        logger.info("[mock-crm] contact upsert: %s → %s", contact.full_name, external_id)
        return external_id

    async def push_progress(self, update: CrmProgressUpdate) -> bool:
        logger.info(
            "[mock-crm] progress: %s — %s (%s%%)",
            update.contact_external_id,
            update.course_title,
            update.progress_percent,
        )
        return True

    async def create_deal(self, title: str, amount: float, contact_external_id: str) -> str | None:
        deal_id = f"mock-deal-{uuid.uuid4().hex[:8]}"
        logger.info("[mock-crm] deal: %s (%s) → %s", title, amount, deal_id)
        return deal_id
