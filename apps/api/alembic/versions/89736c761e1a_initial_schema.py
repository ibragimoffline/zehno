from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '89736c761e1a'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('categories',
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('slug', sa.String(length=140), nullable=False),
    sa.Column('icon', sa.String(length=64), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=True)
    op.create_table('integration_statuses',
    sa.Column('kind', sa.Enum('video', 'payment', 'crm', 'notification', 'storage', name='integrationkind', native_enum=False, length=20), nullable=False),
    sa.Column('provider', sa.String(length=48), nullable=False),
    sa.Column('display_name', sa.String(length=80), nullable=False),
    sa.Column('health', sa.Enum('ok', 'degraded', 'error', 'disabled', name='integrationhealth', native_enum=False, length=20), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_error_message', sa.Text(), nullable=True),
    sa.Column('consecutive_failures', sa.Integer(), nullable=False),
    sa.Column('meta', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('kind', 'provider', name='uq_integration_kind_provider')
    )
    op.create_index(op.f('ix_integration_statuses_kind'), 'integration_statuses', ['kind'], unique=False)
    op.create_index(op.f('ix_integration_statuses_provider'), 'integration_statuses', ['provider'], unique=False)
    op.create_table('organizations',
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('slug', sa.String(length=220), nullable=False),
    sa.Column('type', sa.Enum('school', 'teacher', 'training_center', 'b2b_client', name='organizationtype', native_enum=False, length=20), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('logo_url', sa.String(length=512), nullable=True),
    sa.Column('website', sa.String(length=255), nullable=True),
    sa.Column('contact_email', sa.String(length=255), nullable=True),
    sa.Column('contact_phone', sa.String(length=32), nullable=True),
    sa.Column('owner_id', sa.Uuid(), nullable=True),
    sa.Column('commission_percent', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('seats_purchased', sa.Integer(), nullable=False),
    sa.Column('crm_provider', sa.String(length=32), nullable=True),
    sa.Column('crm_external_id', sa.String(length=128), nullable=True),
    sa.Column('crm_company_id', sa.String(length=128), nullable=True),
    sa.Column('crm_sync_enabled', sa.Boolean(), nullable=False),
    sa.Column('payout_details', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='fk_organizations_owner_id_users', ondelete='SET NULL', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_crm_external_id'), 'organizations', ['crm_external_id'], unique=False)
    op.create_index(op.f('ix_organizations_owner_id'), 'organizations', ['owner_id'], unique=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)
    op.create_index(op.f('ix_organizations_type'), 'organizations', ['type'], unique=False)
    op.create_table('system_settings',
    sa.Column('key', sa.String(length=80), nullable=False),
    sa.Column('value', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_public', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_settings_key'), 'system_settings', ['key'], unique=True)
    op.create_table('users',
    sa.Column('full_name', sa.String(length=160), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=32), nullable=True),
    sa.Column('hashed_password', sa.String(length=255), nullable=True),
    sa.Column('role', sa.Enum('student', 'teacher', 'org_admin', 'b2b_manager', 'admin', name='userrole', native_enum=False, length=20), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=True),
    sa.Column('avatar_url', sa.String(length=512), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('locale', sa.String(length=5), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_blocked', sa.Boolean(), nullable=False),
    sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('telegram_chat_id', sa.String(length=64), nullable=True),
    sa.Column('telegram_link_code', sa.String(length=32), nullable=True),
    sa.Column('google_sub', sa.String(length=255), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('google_sub')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_telegram_chat_id'), 'users', ['telegram_chat_id'], unique=False)
    op.create_index(op.f('ix_users_telegram_link_code'), 'users', ['telegram_link_code'], unique=False)
    op.create_table('audit_logs',
    sa.Column('actor_id', sa.Uuid(), nullable=True),
    sa.Column('actor_email', sa.String(length=255), nullable=True),
    sa.Column('action', sa.String(length=80), nullable=False),
    sa.Column('entity_type', sa.String(length=60), nullable=True),
    sa.Column('entity_id', sa.String(length=60), nullable=True),
    sa.Column('changes', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('ip_address', sa.String(length=64), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_actor_created', 'audit_logs', ['actor_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_table('courses',
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=True),
    sa.Column('category_id', sa.Uuid(), nullable=True),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('slug', sa.String(length=220), nullable=False),
    sa.Column('subtitle', sa.String(length=300), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('cover_url', sa.String(length=512), nullable=True),
    sa.Column('promo_video_url', sa.String(length=512), nullable=True),
    sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('discount_price', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('level', sa.Enum('beginner', 'intermediate', 'advanced', name='courselevel', native_enum=False, length=20), nullable=False),
    sa.Column('language', sa.Enum('uz', 'ru', 'en', name='courselanguage', native_enum=False, length=5), nullable=False),
    sa.Column('status', sa.Enum('draft', 'pending', 'published', 'rejected', 'archived', name='coursestatus', native_enum=False, length=20), nullable=False),
    sa.Column('what_you_learn', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('requirements', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('target_audience', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('has_certificate', sa.Boolean(), nullable=False),
    sa.Column('sequential_progress', sa.Boolean(), nullable=False),
    sa.Column('completion_threshold', sa.Integer(), nullable=False),
    sa.Column('lessons_count', sa.Integer(), nullable=False),
    sa.Column('duration_seconds', sa.Integer(), nullable=False),
    sa.Column('students_count', sa.Integer(), nullable=False),
    sa.Column('rating_avg', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('rating_count', sa.Integer(), nullable=False),
    sa.Column('is_featured', sa.Boolean(), nullable=False),
    sa.Column('is_bestseller', sa.Boolean(), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('rejection_reason', sa.Text(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_courses_category_id'), 'courses', ['category_id'], unique=False)
    op.create_index(op.f('ix_courses_organization_id'), 'courses', ['organization_id'], unique=False)
    op.create_index(op.f('ix_courses_owner_id'), 'courses', ['owner_id'], unique=False)
    op.create_index('ix_courses_owner_status', 'courses', ['owner_id', 'status'], unique=False)
    op.create_index(op.f('ix_courses_slug'), 'courses', ['slug'], unique=True)
    op.create_index(op.f('ix_courses_status'), 'courses', ['status'], unique=False)
    op.create_index('ix_courses_status_published', 'courses', ['status', 'published_at'], unique=False)
    op.create_table('crm_sync_log',
    sa.Column('organization_id', sa.Uuid(), nullable=True),
    sa.Column('user_id', sa.Uuid(), nullable=True),
    sa.Column('provider', sa.String(length=32), nullable=False),
    sa.Column('event_type', sa.String(length=64), nullable=False),
    sa.Column('direction', sa.String(length=16), nullable=False),
    sa.Column('payload', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('response', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('external_id', sa.String(length=128), nullable=True),
    sa.Column('status', sa.Enum('pending', 'success', 'failed', name='crmsyncstatus', native_enum=False, length=20), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crm_sync_log_event_type'), 'crm_sync_log', ['event_type'], unique=False)
    op.create_index(op.f('ix_crm_sync_log_organization_id'), 'crm_sync_log', ['organization_id'], unique=False)
    op.create_index(op.f('ix_crm_sync_log_status'), 'crm_sync_log', ['status'], unique=False)
    op.create_index('ix_crm_sync_org_created', 'crm_sync_log', ['organization_id', 'created_at'], unique=False)
    op.create_table('notification_logs',
    sa.Column('user_id', sa.Uuid(), nullable=True),
    sa.Column('channel', sa.Enum('telegram', 'email', 'push', name='notificationchannel', native_enum=False, length=20), nullable=False),
    sa.Column('template', sa.String(length=64), nullable=False),
    sa.Column('recipient', sa.String(length=255), nullable=True),
    sa.Column('subject', sa.String(length=255), nullable=True),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('context', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('status', sa.Enum('pending', 'sent', 'failed', name='notificationstatus', native_enum=False, length=20), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_logs_status'), 'notification_logs', ['status'], unique=False)
    op.create_index(op.f('ix_notification_logs_template'), 'notification_logs', ['template'], unique=False)
    op.create_index(op.f('ix_notification_logs_user_id'), 'notification_logs', ['user_id'], unique=False)
    op.create_index('ix_notification_user_created', 'notification_logs', ['user_id', 'created_at'], unique=False)
    op.create_table('payout_requests',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('payout_details', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('admin_comment', sa.Text(), nullable=True),
    sa.Column('reviewed_by_id', sa.Uuid(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payout_requests_status'), 'payout_requests', ['status'], unique=False)
    op.create_index(op.f('ix_payout_requests_user_id'), 'payout_requests', ['user_id'], unique=False)
    op.create_table('refresh_tokens',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_hash', sa.String(length=128), nullable=False),
    sa.Column('jti', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('replaced_by_jti', sa.String(length=64), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.Column('ip_address', sa.String(length=64), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_jti'), 'refresh_tokens', ['jti'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index('ix_refresh_tokens_user_active', 'refresh_tokens', ['user_id', 'revoked_at'], unique=False)
    op.create_table('cart_items',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('course_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'course_id', name='uq_cart_user_course')
    )
    op.create_index(op.f('ix_cart_items_user_id'), 'cart_items', ['user_id'], unique=False)
    op.create_table('coupons',
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('type', sa.Enum('percent', 'fixed', name='coupontype', native_enum=False, length=10), nullable=False),
    sa.Column('value', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=True),
    sa.Column('course_id', sa.Uuid(), nullable=True),
    sa.Column('max_redemptions', sa.Integer(), nullable=True),
    sa.Column('redemptions_count', sa.Integer(), nullable=False),
    sa.Column('min_order_total', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coupons_code'), 'coupons', ['code'], unique=True)
    op.create_index(op.f('ix_coupons_course_id'), 'coupons', ['course_id'], unique=False)
    op.create_index(op.f('ix_coupons_owner_id'), 'coupons', ['owner_id'], unique=False)
    op.create_table('course_reviews',
    sa.Column('course_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='reviewstatus', native_enum=False, length=20), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('course_id', 'user_id', name='uq_review_course_user')
    )
    op.create_index(op.f('ix_course_reviews_course_id'), 'course_reviews', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_reviews_status'), 'course_reviews', ['status'], unique=False)
    op.create_table('moderation_logs',
    sa.Column('course_id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=True),
    sa.Column('action', sa.Enum('submit', 'approve', 'reject', 'archive', name='moderationaction', native_enum=False, length=20), nullable=False),
    sa.Column('from_status', sa.String(length=20), nullable=True),
    sa.Column('to_status', sa.String(length=20), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_moderation_logs_course_id'), 'moderation_logs', ['course_id'], unique=False)
    op.create_table('modules',
    sa.Column('course_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_modules_course_order', 'modules', ['course_id', 'order_index'], unique=False)
    op.create_table('lessons',
    sa.Column('module_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('content_type', sa.Enum('video', 'pdf', 'quiz', 'text', name='lessoncontenttype', native_enum=False, length=10), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('duration_seconds', sa.Integer(), nullable=False),
    sa.Column('text_content', sa.Text(), nullable=True),
    sa.Column('attachments', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('is_preview', sa.Boolean(), nullable=False),
    sa.Column('is_published', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lessons_module_order', 'lessons', ['module_id', 'order_index'], unique=False)
    op.create_table('orders',
    sa.Column('order_number', sa.String(length=32), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=True),
    sa.Column('status', sa.Enum('pending', 'paid', 'failed', 'cancelled', 'refunded', name='orderstatus', native_enum=False, length=20), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('discount_total', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('coupon_id', sa.Uuid(), nullable=True),
    sa.Column('bulk_emails', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['coupon_id'], ['coupons.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_orders_organization_id'), 'orders', ['organization_id'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)
    op.create_index('ix_orders_user_status', 'orders', ['user_id', 'status'], unique=False)
    op.create_table('enrollments',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('course_id', sa.Uuid(), nullable=False),
    sa.Column('order_id', sa.Uuid(), nullable=True),
    sa.Column('organization_id', sa.Uuid(), nullable=True),
    sa.Column('source', sa.Enum('individual', 'b2b_bulk', 'manual', 'free', name='enrollmentsource', native_enum=False, length=20), nullable=False),
    sa.Column('status', sa.Enum('active', 'completed', 'expired', 'cancelled', name='enrollmentstatus', native_enum=False, length=20), nullable=False),
    sa.Column('progress_percent', sa.Integer(), nullable=False),
    sa.Column('completed_lessons', sa.Integer(), nullable=False),
    sa.Column('last_lesson_id', sa.Uuid(), nullable=True),
    sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['last_lesson_id'], ['lessons.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'course_id', name='uq_enrollment_user_course')
    )
    op.create_index('ix_enrollments_course_status', 'enrollments', ['course_id', 'status'], unique=False)
    op.create_index(op.f('ix_enrollments_organization_id'), 'enrollments', ['organization_id'], unique=False)
    op.create_index(op.f('ix_enrollments_status'), 'enrollments', ['status'], unique=False)
    op.create_index(op.f('ix_enrollments_user_id'), 'enrollments', ['user_id'], unique=False)
    op.create_table('order_items',
    sa.Column('order_id', sa.Uuid(), nullable=False),
    sa.Column('course_id', sa.Uuid(), nullable=False),
    sa.Column('course_title', sa.String(length=200), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('seller_id', sa.Uuid(), nullable=True),
    sa.Column('commission_percent', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('commission_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('seller_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_table('payments',
    sa.Column('order_id', sa.Uuid(), nullable=False),
    sa.Column('provider', sa.String(length=32), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('status', sa.Enum('pending', 'paid', 'failed', 'refunded', 'cancelled', name='paymentstatus', native_enum=False, length=20), nullable=False),
    sa.Column('transaction_id', sa.String(length=128), nullable=True),
    sa.Column('checkout_url', sa.String(length=1024), nullable=True),
    sa.Column('raw_payload', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('provider', 'transaction_id', name='uq_payment_provider_txn')
    )
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=False)
    op.create_index(op.f('ix_payments_provider'), 'payments', ['provider'], unique=False)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_transaction_id'), 'payments', ['transaction_id'], unique=False)
    op.create_table('quizzes',
    sa.Column('lesson_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=True),
    sa.Column('questions', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('passing_score', sa.Integer(), nullable=False),
    sa.Column('max_attempts', sa.Integer(), nullable=False),
    sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
    sa.Column('shuffle_questions', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('lesson_id')
    )
    op.create_table('video_assets',
    sa.Column('lesson_id', sa.Uuid(), nullable=False),
    sa.Column('provider', sa.String(length=32), nullable=False),
    sa.Column('external_video_id', sa.String(length=255), nullable=False),
    sa.Column('status', sa.Enum('pending_upload', 'processing', 'ready', 'failed', name='videoassetstatus', native_enum=False, length=20), nullable=False),
    sa.Column('duration_seconds', sa.Integer(), nullable=False),
    sa.Column('thumbnail_url', sa.String(length=512), nullable=True),
    sa.Column('original_filename', sa.String(length=255), nullable=True),
    sa.Column('size_bytes', sa.Integer(), nullable=True),
    sa.Column('provider_meta', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('lesson_id')
    )
    op.create_index(op.f('ix_video_assets_external_video_id'), 'video_assets', ['external_video_id'], unique=False)
    op.create_table('certificates',
    sa.Column('enrollment_id', sa.Uuid(), nullable=False),
    sa.Column('certificate_code', sa.String(length=32), nullable=False),
    sa.Column('pdf_url', sa.String(length=1024), nullable=True),
    sa.Column('pdf_object_key', sa.String(length=512), nullable=True),
    sa.Column('verification_url', sa.String(length=512), nullable=True),
    sa.Column('snapshot', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('enrollment_id')
    )
    op.create_index(op.f('ix_certificates_certificate_code'), 'certificates', ['certificate_code'], unique=True)
    op.create_table('lesson_progress',
    sa.Column('enrollment_id', sa.Uuid(), nullable=False),
    sa.Column('lesson_id', sa.Uuid(), nullable=False),
    sa.Column('completed', sa.Boolean(), nullable=False),
    sa.Column('watch_seconds', sa.Integer(), nullable=False),
    sa.Column('last_position_seconds', sa.Integer(), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('enrollment_id', 'lesson_id', name='uq_progress_enrollment_lesson')
    )
    op.create_index(op.f('ix_lesson_progress_enrollment_id'), 'lesson_progress', ['enrollment_id'], unique=False)
    op.create_table('quiz_attempts',
    sa.Column('quiz_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('enrollment_id', sa.Uuid(), nullable=True),
    sa.Column('score', sa.Integer(), nullable=False),
    sa.Column('passed', sa.Boolean(), nullable=False),
    sa.Column('answers', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('attempt_number', sa.Integer(), nullable=False),
    sa.Column('attempted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quiz_attempts_quiz_user', 'quiz_attempts', ['quiz_id', 'user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_quiz_attempts_quiz_user', table_name='quiz_attempts')
    op.drop_table('quiz_attempts')
    op.drop_index(op.f('ix_lesson_progress_enrollment_id'), table_name='lesson_progress')
    op.drop_table('lesson_progress')
    op.drop_index(op.f('ix_certificates_certificate_code'), table_name='certificates')
    op.drop_table('certificates')
    op.drop_index(op.f('ix_video_assets_external_video_id'), table_name='video_assets')
    op.drop_table('video_assets')
    op.drop_table('quizzes')
    op.drop_index(op.f('ix_payments_transaction_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_provider'), table_name='payments')
    op.drop_index(op.f('ix_payments_order_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_index(op.f('ix_order_items_order_id'), table_name='order_items')
    op.drop_table('order_items')
    op.drop_index(op.f('ix_enrollments_user_id'), table_name='enrollments')
    op.drop_index(op.f('ix_enrollments_status'), table_name='enrollments')
    op.drop_index(op.f('ix_enrollments_organization_id'), table_name='enrollments')
    op.drop_index('ix_enrollments_course_status', table_name='enrollments')
    op.drop_table('enrollments')
    op.drop_index('ix_orders_user_status', table_name='orders')
    op.drop_index(op.f('ix_orders_user_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_index(op.f('ix_orders_organization_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_order_number'), table_name='orders')
    op.drop_table('orders')
    op.drop_index('ix_lessons_module_order', table_name='lessons')
    op.drop_table('lessons')
    op.drop_index('ix_modules_course_order', table_name='modules')
    op.drop_table('modules')
    op.drop_index(op.f('ix_moderation_logs_course_id'), table_name='moderation_logs')
    op.drop_table('moderation_logs')
    op.drop_index(op.f('ix_course_reviews_status'), table_name='course_reviews')
    op.drop_index(op.f('ix_course_reviews_course_id'), table_name='course_reviews')
    op.drop_table('course_reviews')
    op.drop_index(op.f('ix_coupons_owner_id'), table_name='coupons')
    op.drop_index(op.f('ix_coupons_course_id'), table_name='coupons')
    op.drop_index(op.f('ix_coupons_code'), table_name='coupons')
    op.drop_table('coupons')
    op.drop_index(op.f('ix_cart_items_user_id'), table_name='cart_items')
    op.drop_table('cart_items')
    op.drop_index('ix_refresh_tokens_user_active', table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_jti'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index(op.f('ix_payout_requests_user_id'), table_name='payout_requests')
    op.drop_index(op.f('ix_payout_requests_status'), table_name='payout_requests')
    op.drop_table('payout_requests')
    op.drop_index('ix_notification_user_created', table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_user_id'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_template'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_status'), table_name='notification_logs')
    op.drop_table('notification_logs')
    op.drop_index('ix_crm_sync_org_created', table_name='crm_sync_log')
    op.drop_index(op.f('ix_crm_sync_log_status'), table_name='crm_sync_log')
    op.drop_index(op.f('ix_crm_sync_log_organization_id'), table_name='crm_sync_log')
    op.drop_index(op.f('ix_crm_sync_log_event_type'), table_name='crm_sync_log')
    op.drop_table('crm_sync_log')
    op.drop_index('ix_courses_status_published', table_name='courses')
    op.drop_index(op.f('ix_courses_status'), table_name='courses')
    op.drop_index(op.f('ix_courses_slug'), table_name='courses')
    op.drop_index('ix_courses_owner_status', table_name='courses')
    op.drop_index(op.f('ix_courses_owner_id'), table_name='courses')
    op.drop_index(op.f('ix_courses_organization_id'), table_name='courses')
    op.drop_index(op.f('ix_courses_category_id'), table_name='courses')
    op.drop_table('courses')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index('ix_audit_actor_created', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_users_telegram_link_code'), table_name='users')
    op.drop_index(op.f('ix_users_telegram_chat_id'), table_name='users')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_phone'), table_name='users')
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_system_settings_key'), table_name='system_settings')
    op.drop_table('system_settings')
    op.drop_index(op.f('ix_organizations_type'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_owner_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_crm_external_id'), table_name='organizations')
    op.drop_table('organizations')
    op.drop_index(op.f('ix_integration_statuses_provider'), table_name='integration_statuses')
    op.drop_index(op.f('ix_integration_statuses_kind'), table_name='integration_statuses')
    op.drop_table('integration_statuses')
    op.drop_index(op.f('ix_categories_slug'), table_name='categories')
    op.drop_table('categories')
