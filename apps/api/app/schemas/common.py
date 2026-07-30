"""Umumiy Pydantic sxemalar."""

from __future__ import annotations

from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    """SQLAlchemy obyektidan to'g'ridan-to'g'ri o'qish uchun asos."""

    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str
    ok: bool = True


class IdResponse(BaseModel):
    id: str


class Page(BaseModel, Generic[T]):  # noqa: UP046 - PEP 695 sintaksisi pydantic bilan hali to'liq mos emas
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, page: int, per_page: int) -> Page[T]:
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=ceil(total / per_page) if per_page else 0,
        )


class SortOrder(BaseModel):
    sort: str = Field(
        default="newest", description="newest | popular | price_asc | price_desc | rating"
    )
