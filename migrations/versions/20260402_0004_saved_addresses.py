# -*- coding: utf-8 -*-
"""Phase 3: saved addresses table."""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0004"
down_revision = "20260402_0003"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _table_exists("addresses"):
        op.create_table(
            "addresses",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("label", sa.String(length=80), nullable=False, server_default=""),
            sa.Column("address_text", sa.Text(), nullable=False, server_default=""),
            sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
            sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    if not _index_exists("addresses", "ix_addresses_user_id"):
        op.create_index("ix_addresses_user_id", "addresses", ["user_id"], unique=False)
    if not _index_exists("addresses", "ix_addresses_is_default"):
        op.create_index("ix_addresses_is_default", "addresses", ["is_default"], unique=False)


def downgrade() -> None:
    if _table_exists("addresses"):
        if _index_exists("addresses", "ix_addresses_is_default"):
            op.drop_index("ix_addresses_is_default", table_name="addresses")
        if _index_exists("addresses", "ix_addresses_user_id"):
            op.drop_index("ix_addresses_user_id", table_name="addresses")
        op.drop_table("addresses")
