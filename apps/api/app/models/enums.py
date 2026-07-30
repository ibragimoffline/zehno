from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    student = "student"
    teacher = "teacher"
    org_admin = "org_admin"
    b2b_manager = "b2b_manager"
    admin = "admin"


class OrganizationType(StrEnum):
    school = "school"
    teacher = "teacher"
    training_center = "training_center"
    b2b_client = "b2b_client"


class CourseStatus(StrEnum):
    draft = "draft"
    pending = "pending"
    published = "published"
    rejected = "rejected"
    archived = "archived"


class CourseLevel(StrEnum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class CourseLanguage(StrEnum):
    uz = "uz"
    ru = "ru"
    en = "en"


class LessonContentType(StrEnum):
    video = "video"
    pdf = "pdf"
    quiz = "quiz"
    text = "text"


class VideoAssetStatus(StrEnum):
    pending_upload = "pending_upload"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class EnrollmentSource(StrEnum):
    individual = "individual"
    b2b_bulk = "b2b_bulk"
    manual = "manual"
    free = "free"


class EnrollmentStatus(StrEnum):
    active = "active"
    completed = "completed"
    expired = "expired"
    cancelled = "cancelled"


class OrderStatus(StrEnum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    cancelled = "cancelled"
    refunded = "refunded"


class PaymentStatus(StrEnum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"
    cancelled = "cancelled"


class CouponType(StrEnum):
    percent = "percent"
    fixed = "fixed"


class ReviewStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CrmSyncStatus(StrEnum):
    pending = "pending"
    success = "success"
    failed = "failed"


class NotificationChannel(StrEnum):
    telegram = "telegram"
    email = "email"
    push = "push"


class NotificationStatus(StrEnum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class ModerationAction(StrEnum):
    submit = "submit"
    approve = "approve"
    reject = "reject"
    archive = "archive"


class IntegrationKind(StrEnum):
    video = "video"
    payment = "payment"
    crm = "crm"
    notification = "notification"
    storage = "storage"


class IntegrationHealth(StrEnum):
    ok = "ok"
    degraded = "degraded"
    error = "error"
    disabled = "disabled"
