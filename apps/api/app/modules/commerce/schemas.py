"""Commerce sxemalari."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import CouponType, OrderStatus, PaymentStatus
from app.modules.courses.schemas import CourseCard
from app.schemas.common import ORMModel


class CartItemView(ORMModel):
    id: uuid.UUID
    course: CourseCard
    created_at: datetime


class CartSummary(BaseModel):
    items: list[CartItemView]
    subtotal: Decimal
    discount_total: Decimal = Decimal("0")
    total: Decimal
    currency: str = "UZS"
    coupon_code: str | None = None


class AddToCartRequest(BaseModel):
    course_id: uuid.UUID


class CheckoutRequest(BaseModel):
    course_ids: list[uuid.UUID] | None = Field(
        default=None,
        description="Bo'sh bo'lsa savatdagi barcha kurslar olinadi",
    )
    coupon_code: str | None = Field(default=None, max_length=40)
    provider: str | None = Field(
        default=None, description="payme | click | mock (bo'sh bo'lsa .env dagi default)"
    )
    return_url: str | None = Field(default=None, max_length=512)


class OrderItemView(ORMModel):
    id: uuid.UUID
    course_id: uuid.UUID
    course_title: str
    unit_price: Decimal
    quantity: int


class OrderView(ORMModel):
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    subtotal: Decimal
    discount_total: Decimal
    total: Decimal
    currency: str
    items: list[OrderItemView] = []
    paid_at: datetime | None = None
    created_at: datetime


class CheckoutResponse(BaseModel):
    order: OrderView
    checkout_url: str
    provider: str
    payment_id: uuid.UUID
    is_free: bool = False


class PaymentView(ORMModel):
    id: uuid.UUID
    provider: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    transaction_id: str | None = None
    checkout_url: str | None = None
    paid_at: datetime | None = None
    created_at: datetime


# ------------------------------------------------------------------ kuponlar
class CouponCreate(BaseModel):
    code: str | None = Field(default=None, max_length=40)
    type: CouponType = CouponType.percent
    value: Decimal = Field(gt=0)
    course_id: uuid.UUID | None = None
    max_redemptions: int | None = Field(default=None, ge=1)
    min_order_total: Decimal | None = Field(default=None, ge=0)
    starts_at: datetime | None = None
    expires_at: datetime | None = None


class CouponView(ORMModel):
    id: uuid.UUID
    code: str
    type: CouponType
    value: Decimal
    course_id: uuid.UUID | None = None
    max_redemptions: int | None = None
    redemptions_count: int = 0
    min_order_total: Decimal | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool
    created_at: datetime


class CouponValidateRequest(BaseModel):
    code: str = Field(max_length=40)
    course_ids: list[uuid.UUID] | None = None


class CouponValidateResponse(BaseModel):
    valid: bool
    discount: Decimal = Decimal("0")
    message: str
    coupon: CouponView | None = None


# ------------------------------------------------------------------ B2B
class BulkEnrollRequest(BaseModel):
    course_ids: list[uuid.UUID] = Field(min_length=1)
    emails: list[EmailStr] = Field(min_length=1, max_length=500)
    send_invites: bool = True


class BulkEnrollResult(BaseModel):
    enrolled: int
    created_users: int
    skipped: list[str] = []
    seats_used: int = 0
    seats_available: int | None = None


# ------------------------------------------------------------------ daromad
class EarningsSummary(BaseModel):
    gross_total: Decimal
    commission_total: Decimal
    net_total: Decimal
    pending_payout: Decimal
    paid_out: Decimal
    currency: str = "UZS"
    sales_count: int
    students_count: int


class EarningsPoint(BaseModel):
    date: str
    gross: Decimal
    net: Decimal
    sales: int


class PayoutRequestCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    payout_details: dict | None = None


class PayoutRequestView(ORMModel):
    id: uuid.UUID
    amount: Decimal
    currency: str
    status: str
    admin_comment: str | None = None
    requested_at: datetime
    reviewed_at: datetime | None = None
