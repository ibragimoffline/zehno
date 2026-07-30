from __future__ import annotations

from sqlalchemy import JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB

UUIDType = Uuid(as_uuid=True)

JSONType = JSON().with_variant(JSONB(), "postgresql")
