# -*- coding: utf-8 -*-
"""Phase 2: order status normalization and cash payment method."""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0003"
down_revision = "20260328_0002"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _normalize_status_sql(column_name: str) -> str:
    return (
        f"CASE "
        f"WHEN lower({column_name}) = 'created' THEN 'pending' "
        f"WHEN lower({column_name}) = 'paid' THEN 'confirmed' "
        f"WHEN lower({column_name}) = 'in_progress' THEN 'preparing' "
        f"WHEN lower({column_name}) = 'confirm' THEN 'confirmed' "
        f"ELSE lower({column_name}) END"
    )


def upgrade() -> None:
    if _table_exists("orders"):
        if not _column_exists("orders", "payment_method"):
            op.add_column(
                "orders",
                sa.Column("payment_method", sa.String(length=20), nullable=False, server_default="cash"),
            )
        if not _index_exists("orders", "ix_orders_payment_method"):
            op.create_index("ix_orders_payment_method", "orders", ["payment_method"], unique=False)
        op.execute("UPDATE orders SET payment_method = 'cash' WHERE payment_method IS NULL OR payment_method = ''")
        op.execute(
            f"UPDATE orders SET status = {_normalize_status_sql('status')}"
        )

    if _table_exists("order_status_history"):
        op.execute(
            f"UPDATE order_status_history SET old_status = {_normalize_status_sql('old_status')}"
        )
        op.execute(
            f"UPDATE order_status_history SET new_status = {_normalize_status_sql('new_status')}"
        )


def downgrade() -> None:
    if _table_exists("orders"):
        if _index_exists("orders", "ix_orders_payment_method"):
            op.drop_index("ix_orders_payment_method", table_name="orders")
        if _column_exists("orders", "payment_method"):
            with op.batch_alter_table("orders") as batch_op:
                batch_op.drop_column("payment_method")
