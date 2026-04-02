# -*- coding: utf-8 -*-
"""Add order status history table."""

from alembic import op
import sqlalchemy as sa


revision = "20260328_0002"
down_revision = "20260327_0001"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def upgrade() -> None:
    if not _table_exists("order_status_history"):
        op.create_table(
            "order_status_history",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
            sa.Column("old_status", sa.String(length=32), nullable=False, server_default=""),
            sa.Column("new_status", sa.String(length=32), nullable=False),
            sa.Column("changed_by", sa.String(length=128), nullable=False, server_default=""),
            sa.Column("notes", sa.Text(), nullable=False, server_default=""),
            sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    if not _index_exists("order_status_history", "ix_order_status_history_order_id"):
        op.create_index("ix_order_status_history_order_id", "order_status_history", ["order_id"], unique=False)


def downgrade() -> None:
    if _table_exists("order_status_history"):
        if _index_exists("order_status_history", "ix_order_status_history_order_id"):
            op.drop_index("ix_order_status_history_order_id", table_name="order_status_history")
        op.drop_table("order_status_history")
