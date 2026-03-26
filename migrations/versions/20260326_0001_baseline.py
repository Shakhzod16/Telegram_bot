# -*- coding: utf-8 -*-
"""Baseline migration for the Telegram food delivery schema."""

from alembic import op


revision = "20260326_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders (user_id)")
    connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_payments_order_id ON payments (order_id)")


def downgrade() -> None:
    connection = op.get_bind()
    connection.exec_driver_sql("DROP INDEX IF EXISTS ix_orders_user_id")
    connection.exec_driver_sql("DROP INDEX IF EXISTS ix_payments_order_id")
