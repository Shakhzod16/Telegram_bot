# -*- coding: utf-8 -*-
from __future__ import annotations

from backend.repositories.cart_repo import CartRepository


class CartService:
    def __init__(self, cart_repo: CartRepository) -> None:
        self.cart_repo = cart_repo

    async def add_item(self, user_id: int, product_id: int, qty: int):
        return await self.cart_repo.add_item(user_id=user_id, product_id=product_id, qty=qty)

    async def remove_item(self, user_id: int, item_id: int) -> bool:
        items = await self.cart_repo.get_by_user(user_id)
        allowed_ids = {item.id for item in items}
        if item_id not in allowed_ids:
            return False
        return await self.cart_repo.remove_item(item_id)

    async def calculate_total(self, user_id: int) -> int:
        items = await self.cart_repo.get_by_user(user_id)
        return sum(item.total_price for item in items)

    async def clear(self, user_id: int) -> int:
        return await self.cart_repo.clear(user_id)

    @staticmethod
    def from_order(order_items, active_product_ids: set[int]) -> tuple[list[dict], list[str]]:
        cart_items: list[dict] = []
        skipped: list[str] = []
        aggregated: dict[int, int] = {}
        for item in order_items:
            product_id = int(item.product_id)
            aggregated[product_id] = aggregated.get(product_id, 0) + int(item.quantity)
        for product_id, quantity in aggregated.items():
            if product_id not in active_product_ids:
                source_name = next(
                    (line.product_name for line in order_items if int(line.product_id) == product_id and line.product_name),
                    "",
                )
                skipped.append(source_name or f"Product #{product_id}")
                continue
            cart_items.append({"product_id": product_id, "quantity": quantity})
        return cart_items, skipped
