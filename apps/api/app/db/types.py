"""Dialektga bog'liq bo'lmagan ustun tiplari.

Production'da PostgreSQL ishlatiladi (UUID + JSONB), lekin testlarni SQLite'da
tez o'tkazish imkoniyatini yo'qotmaslik uchun tiplar variant orqali beriladi.
"""

from __future__ import annotations

from sqlalchemy import JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB

#: PostgreSQL'da native `uuid`, boshqa dialektlarda `CHAR(32)`
UUIDType = Uuid(as_uuid=True)

#: PostgreSQL'da `jsonb`, boshqa dialektlarda oddiy `json`
JSONType = JSON().with_variant(JSONB(), "postgresql")
