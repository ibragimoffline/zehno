"""EspoCRM adapteri (to'liq bepul, self-hosted, cheklovsiz foydalanuvchi).

Autentifikatsiya: `X-Api-Key` header. REST endpointlar: `/api/v1/Contact`,
`/api/v1/Account`, `/api/v1/Note` (stream comment).
"""

from __future__ import annotations

import logging

from app.core.config import settings
from app.core.exceptions import IntegrationError
from app.integrations.crm.base import CrmCompany, CrmContact, CrmProgressUpdate, CrmProvider

logger = logging.getLogger(__name__)


class EspoCrmProvider(CrmProvider):
    provider_name = "espocrm"
    display_name = "EspoCRM"

    def is_configured(self) -> bool:
        return bool(settings.ESPOCRM_BASE_URL and settings.ESPOCRM_API_KEY)

    @property
    def _base(self) -> str:
        if not self.is_configured():
            raise IntegrationError("EspoCRM sozlanmagan", provider=self.provider_name)
        return (settings.ESPOCRM_BASE_URL or "").rstrip("/") + "/api/v1"

    def _headers(self) -> dict[str, str]:
        return {
            "X-Api-Key": settings.ESPOCRM_API_KEY or "",
            "Content-Type": "application/json",
        }

    async def upsert_company(self, company: CrmCompany) -> str:
        payload = {
            "name": company.name,
            "emailAddress": company.email,
            "phoneNumber": company.phone,
            "website": company.website,
            **company.custom_fields,
        }
        if company.external_id:
            await self._request(
                "PUT",
                f"{self._base}/Account/{company.external_id}",
                headers=self._headers(),
                json=payload,
            )
            return company.external_id

        response = await self._request(
            "POST", f"{self._base}/Account", headers=self._headers(), json=payload
        )
        return str(response.json()["id"])

    async def upsert_contact(self, contact: CrmContact) -> str:
        first, _, last = contact.full_name.partition(" ")
        payload = {
            "firstName": first,
            "lastName": last or first,
            "emailAddress": contact.email,
            "phoneNumber": contact.phone,
            **contact.custom_fields,
        }
        if contact.company_external_id:
            payload["accountId"] = contact.company_external_id

        if contact.external_id:
            await self._request(
                "PUT",
                f"{self._base}/Contact/{contact.external_id}",
                headers=self._headers(),
                json=payload,
            )
            return contact.external_id

        response = await self._request(
            "POST", f"{self._base}/Contact", headers=self._headers(), json=payload
        )
        return str(response.json()["id"])

    async def push_progress(self, update: CrmProgressUpdate) -> bool:
        body = (
            f"Kurs: {update.course_title}\n"
            f"Progress: {update.progress_percent}%\n"
            f"{'Tugallandi' if update.completed else 'Davom etmoqda'}"
        )
        if update.certificate_code:
            body += f"\nSertifikat: {update.certificate_code}"

        await self._request(
            "POST",
            f"{self._base}/Note",
            headers=self._headers(),
            json={
                "type": "Post",
                "post": body,
                "parentType": "Contact",
                "parentId": update.contact_external_id,
            },
        )
        return True

    async def healthcheck(self) -> tuple[bool, str | None]:
        if not self.is_configured():
            return False, "EspoCRM sozlanmagan"
        try:
            await self._request("GET", f"{self._base}/App/user", headers=self._headers())
            return True, None
        except IntegrationError as exc:
            return False, str(exc)
