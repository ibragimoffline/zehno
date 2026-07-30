from __future__ import annotations

import logging

from app.core.config import settings
from app.core.exceptions import IntegrationError
from app.integrations.crm.base import (
    CrmCompany,
    CrmContact,
    CrmProgressUpdate,
    CrmProvider,
)

logger = logging.getLogger(__name__)


class Bitrix24Provider(CrmProvider):
    provider_name = "bitrix24"
    display_name = "Bitrix24"

    def is_configured(self) -> bool:
        return bool(settings.BITRIX24_WEBHOOK_URL)

    @property
    def _base(self) -> str:
        if not self.is_configured():
            raise IntegrationError(
                "Bitrix24 sozlanmagan (BITRIX24_WEBHOOK_URL)", provider=self.provider_name
            )
        return (settings.BITRIX24_WEBHOOK_URL or "").rstrip("/")

    async def _call(self, method: str, payload: dict) -> dict:
        try:
            response = await self._request("POST", f"{self._base}/{method}.json", json=payload)
        except IntegrationError as exc:
            raise IntegrationError(
                f"Bitrix24 `{method}`: {_explain(exc.details)}",
                provider=self.provider_name,
                details=exc.details,
            ) from exc

        data = response.json()
        if "error" in data:
            raise IntegrationError(
                f"Bitrix24 `{method}`: {data.get('error_description') or data['error']}",
                provider=self.provider_name,
            )
        return data

    async def scopes(self) -> list[str]:
        data = await self._call("scope", {})
        return [scope for scope in (data.get("result") or []) if scope]

    async def upsert_company(self, company: CrmCompany) -> str:
        if company.external_id:
            await self._call(
                "crm.company.update",
                {
                    "id": company.external_id,
                    "fields": {
                        "TITLE": company.name,
                        **_company_contacts(company),
                        **company.custom_fields,
                    },
                },
            )
            return company.external_id

        data = await self._call(
            "crm.company.add",
            {
                "fields": {
                    "TITLE": company.name,
                    "COMPANY_TYPE": "CUSTOMER",
                    **_company_contacts(company),
                    **company.custom_fields,
                },
                "params": {"REGISTER_SONET_EVENT": "N"},
            },
        )
        return str(data["result"])

    async def upsert_contact(self, contact: CrmContact) -> str:
        fields: dict = {"NAME": contact.full_name, **contact.custom_fields}
        if contact.email:
            fields["EMAIL"] = [{"VALUE": contact.email, "VALUE_TYPE": "WORK"}]
        if contact.phone:
            fields["PHONE"] = [{"VALUE": contact.phone, "VALUE_TYPE": "MOBILE"}]
        if contact.company_external_id:
            fields["COMPANY_ID"] = contact.company_external_id

        if contact.external_id:
            await self._call("crm.contact.update", {"id": contact.external_id, "fields": fields})
            return contact.external_id

        if contact.email:
            found = await self._call(
                "crm.contact.list",
                {"filter": {"EMAIL": contact.email}, "select": ["ID"]},
            )
            results = found.get("result") or []
            if results:
                contact_id = str(results[0]["ID"])
                await self._call("crm.contact.update", {"id": contact_id, "fields": fields})
                return contact_id

        data = await self._call(
            "crm.contact.add",
            {"fields": fields, "params": {"REGISTER_SONET_EVENT": "N"}},
        )
        return str(data["result"])

    async def push_progress(self, update: CrmProgressUpdate) -> bool:
        lines = [
            f"📚 Kurs: {update.course_title}",
            f"📊 Progress: {update.progress_percent}%",
        ]
        if update.quiz_score is not None:
            lines.append(f"✅ Test natijasi: {update.quiz_score}")
        if update.completed:
            lines.append("🎉 Kurs tugallandi")
        if update.certificate_code:
            lines.append(f"🏅 Sertifikat: {update.certificate_code}")
        if update.comment:
            lines.append(update.comment)

        await self._call(
            "crm.timeline.comment.add",
            {
                "fields": {
                    "ENTITY_ID": update.contact_external_id,
                    "ENTITY_TYPE": "contact",
                    "COMMENT": "\n".join(lines),
                }
            },
        )
        return True

    async def create_deal(self, title: str, amount: float, contact_external_id: str) -> str | None:
        data = await self._call(
            "crm.deal.add",
            {
                "fields": {
                    "TITLE": title,
                    "OPPORTUNITY": amount,
                    "CURRENCY_ID": "UZS",
                    "CONTACT_ID": contact_external_id,
                    "STAGE_ID": "NEW",
                },
                "params": {"REGISTER_SONET_EVENT": "N"},
            },
        )
        return str(data["result"])

    async def healthcheck(self) -> tuple[bool, str | None]:
        if not self.is_configured():
            return False, "Bitrix24 sozlanmagan"
        try:
            await self._call("profile", {})
            return True, None
        except IntegrationError as exc:
            return False, str(exc)


def _company_contacts(company: CrmCompany) -> dict:
    fields: dict = {}
    if company.email:
        fields["EMAIL"] = [{"VALUE": company.email, "VALUE_TYPE": "WORK"}]
    if company.phone:
        fields["PHONE"] = [{"VALUE": company.phone, "VALUE_TYPE": "WORK"}]
    if company.website:
        fields["WEB"] = [{"VALUE": company.website, "VALUE_TYPE": "WORK"}]
    return fields


def _explain(details: object) -> str:
    raw = str(details or "")
    if "insufficient_scope" in raw:
        return (
            "webhook tokenida yetarli ruxsat yo'q. Bitrix24 portalida webhook sozlamalarini "
            "oching va `crm` ruxsatini belgilang (Contact, Company, Deal, Timeline)"
        )
    if "invalid_token" in raw or "NO_AUTH_FOUND" in raw:
        return "webhook URL yaroqsiz yoki o'chirilgan"
    if "QUERY_LIMIT_EXCEEDED" in raw:
        return "so'rovlar chegarasi oshdi (sekundiga 2 ta) — keyinroq qayta urinamiz"
    return raw[:200] or "noma'lum xatolik"
