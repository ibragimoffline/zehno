"""add organizations owner fk

`organizations.owner_id` -> `users.id` cheklovi boshlang'ich migratsiyada
yaratilmagan edi: model darajasida FK `use_alter=True` bilan belgilangan
(users <-> organizations aylanaviy bog'liqligini uzish uchun), SQLAlchemy esa
bunday cheklovni `CREATE TABLE` ichida chiqarmaydi va uni keyin alohida
`ALTER TABLE` orqali qo'shish kerak. Natijada baza tomonida cheklov umuman
mavjud emas edi.

Revision ID: 448363c0416f
Revises: 89736c761e1a
Create Date: 2026-07-30 22:38:38.670678

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "448363c0416f"
down_revision: str | None = "89736c761e1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT = "fk_organizations_owner_id_users"


def upgrade() -> None:
    op.create_foreign_key(
        CONSTRAINT,
        source_table="organizations",
        referent_table="users",
        local_cols=["owner_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT, "organizations", type_="foreignkey")
