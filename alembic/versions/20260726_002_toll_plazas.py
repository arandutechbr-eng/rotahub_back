"""Criar tabela toll_plazas.

Revision ID: 20260726_002_toll_plazas
Revises: 20260724_001_users
Create Date: 2026-07-26 08:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260726_002_toll_plazas"
down_revision: str | None = "20260724_001_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "toll_plazas",
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("road", sa.String(length=160), nullable=False),
        sa.Column("concessionaire", sa.String(length=120), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("tariff_per_axle", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_toll_plazas_code"), "toll_plazas", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_toll_plazas_code"), table_name="toll_plazas")
    op.drop_table("toll_plazas")
