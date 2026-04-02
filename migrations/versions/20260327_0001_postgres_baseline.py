# -*- coding: utf-8 -*-
"""PostgreSQL baseline with SQLAlchemy ORM tables."""

from alembic import op
import sqlalchemy as sa


revision = "20260327_0001"
down_revision = None
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


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], *, unique: bool = False) -> None:
    if _index_exists(table_name, index_name):
        return
    op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    if not _table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("telegram_user_id", sa.Integer(), nullable=False),
            sa.Column("first_name", sa.String(length=128), nullable=False, server_default=""),
            sa.Column("last_name", sa.String(length=128), nullable=False, server_default=""),
            sa.Column("username", sa.String(length=128), nullable=False, server_default=""),
            sa.Column("phone", sa.String(length=40), nullable=False, server_default=""),
            sa.Column("language", sa.String(length=8), nullable=False, server_default="en"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    _create_index_if_missing("ix_users_telegram_user_id", "users", ["telegram_user_id"], unique=True)
    _create_index_if_missing("ix_users_language", "users", ["language"], unique=False)

    if not _table_exists("products"):
        op.create_table(
            "products",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("category", sa.String(length=40), nullable=False),
            sa.Column("name_uz", sa.String(length=255), nullable=False),
            sa.Column("name_ru", sa.String(length=255), nullable=False),
            sa.Column("name_en", sa.String(length=255), nullable=False),
            sa.Column("description_uz", sa.Text(), nullable=False, server_default=""),
            sa.Column("description_ru", sa.Text(), nullable=False, server_default=""),
            sa.Column("description_en", sa.Text(), nullable=False, server_default=""),
            sa.Column("price", sa.Integer(), nullable=False),
            sa.Column("image_url", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    _create_index_if_missing("ix_products_category", "products", ["category"], unique=False)
    _create_index_if_missing("ix_products_is_active", "products", ["is_active"], unique=False)

    if not _table_exists("orders"):
        op.create_table(
            "orders",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("total_amount", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(length=8), nullable=False, server_default="UZS"),
            sa.Column("location_label", sa.Text(), nullable=False, server_default=""),
            sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
            sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
            sa.Column("pending_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    _create_index_if_missing("ix_orders_user_id", "orders", ["user_id"], unique=False)
    _create_index_if_missing("ix_orders_status", "orders", ["status"], unique=False)

    if not _table_exists("order_items"):
        op.create_table(
            "order_items",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
            sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Integer(), nullable=False),
            sa.Column("total_price", sa.Integer(), nullable=False),
            sa.Column("product_name", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    _create_index_if_missing("ix_order_items_order_id", "order_items", ["order_id"], unique=False)

    if not _table_exists("payments"):
        op.create_table(
            "payments",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
            sa.Column("provider", sa.String(length=20), nullable=False),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("payment_url", sa.Text(), nullable=False, server_default=""),
            sa.Column("external_id", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("raw_payload", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    _create_index_if_missing("ix_payments_order_id", "payments", ["order_id"], unique=False)
    _create_index_if_missing("ix_payments_provider", "payments", ["provider"], unique=False)
    _create_index_if_missing("ix_payments_status", "payments", ["status"], unique=False)
    _create_index_if_missing("ix_payments_external_id", "payments", ["external_id"], unique=False)


def downgrade() -> None:
    if _table_exists("payments"):
        if _index_exists("payments", "ix_payments_external_id"):
            op.drop_index("ix_payments_external_id", table_name="payments")
        if _index_exists("payments", "ix_payments_status"):
            op.drop_index("ix_payments_status", table_name="payments")
        if _index_exists("payments", "ix_payments_provider"):
            op.drop_index("ix_payments_provider", table_name="payments")
        if _index_exists("payments", "ix_payments_order_id"):
            op.drop_index("ix_payments_order_id", table_name="payments")
        op.drop_table("payments")
    if _table_exists("order_items"):
        if _index_exists("order_items", "ix_order_items_order_id"):
            op.drop_index("ix_order_items_order_id", table_name="order_items")
        op.drop_table("order_items")
    if _table_exists("orders"):
        if _index_exists("orders", "ix_orders_status"):
            op.drop_index("ix_orders_status", table_name="orders")
        if _index_exists("orders", "ix_orders_user_id"):
            op.drop_index("ix_orders_user_id", table_name="orders")
        op.drop_table("orders")
    if _table_exists("products"):
        if _index_exists("products", "ix_products_is_active"):
            op.drop_index("ix_products_is_active", table_name="products")
        if _index_exists("products", "ix_products_category"):
            op.drop_index("ix_products_category", table_name="products")
        op.drop_table("products")
    if _table_exists("users"):
        if _index_exists("users", "ix_users_language"):
            op.drop_index("ix_users_language", table_name="users")
        if _index_exists("users", "ix_users_telegram_user_id"):
            op.drop_index("ix_users_telegram_user_id", table_name="users")
        op.drop_table("users")
