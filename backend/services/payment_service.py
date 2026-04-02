# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import UTC, datetime
from urllib.parse import parse_qsl

from fastapi import HTTPException, Request

from backend.models import OrderStatus, PaymentMethod
from backend.repositories.order_repo import OrderRepository
from backend.repositories.payment_repo import PaymentRepository
from backend.schemas.payment import PaymentCallbackPayload
from backend.security import (
    validate_click_signature,
    validate_internal_callback_signature,
    validate_payme_authorization,
)
from backend.services.notification_service import NotificationService
from backend.services.order_service import OrderService
from config.settings import settings
from utils.logger import get_logger
from utils.texts import t


class PaymeServiceError(Exception):
    def __init__(self, code: int, message: str, data: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class PaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        order_repo: OrderRepository,
        order_service: OrderService,
        notification_service: NotificationService,
    ) -> None:
        self.payment_repo = payment_repo
        self.order_repo = order_repo
        self.order_service = order_service
        self.notification = notification_service
        self.log = get_logger("backend.services.payment")

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(UTC).timestamp() * 1000)

    def generate_click_url(self, order_id: int, amount: int) -> str:
        return (
            "https://my.click.uz/services/pay?"
            f"service_id={settings.click_service_id}&merchant_id={settings.click_merchant_id}"
            f"&amount={amount}&transaction_param={order_id}"
        )

    def verify_click_sign(self, params: dict) -> bool:
        return validate_click_signature(params)

    # Backward-compatible alias.
    def verify_click_hash(self, params: dict) -> bool:
        return self.verify_click_sign(params)

    def generate_payme_url(self, order_id: int, amount: int) -> str:
        import base64

        account = json.dumps({"m": settings.payme_merchant_id, "ac.order_id": order_id, "a": amount})
        encoded = base64.urlsafe_b64encode(account.encode()).decode().rstrip("=")
        return f"{settings.payme_checkout_url}/{encoded}"

    @staticmethod
    def verify_payme_auth(value: str) -> bool:
        return validate_payme_authorization(value)

    @staticmethod
    def _amount_sum_from_tiyin(amount_tiyin: int) -> int:
        return int(amount_tiyin // 100)

    async def _upsert_payment(
        self,
        *,
        provider: str,
        order_id: int,
        amount: int,
        status: str,
        payment_url: str = "",
        external_id: str = "",
        raw_payload: str = "",
    ):
        existing = await self.payment_repo.get_by_external_id(provider=provider, external_id=external_id) if external_id else None
        if existing:
            existing.status = status if status else existing.status
            existing.amount = amount or existing.amount
            if payment_url:
                existing.payment_url = payment_url
            if raw_payload:
                existing.raw_payload = raw_payload[:4000]
            await self.payment_repo.session.flush()
            return existing

        by_order = await self.payment_repo.get_last_by_order_and_provider(order_id=order_id, provider=provider)
        if by_order and by_order.status in {"pending", "paid", "awaiting_cash", "cash_received"}:
            if external_id and not by_order.external_id:
                by_order.external_id = external_id
            if raw_payload:
                by_order.raw_payload = raw_payload[:4000]
            if status and by_order.status != "paid":
                by_order.status = status
            await self.payment_repo.session.flush()
            return by_order

        created = await self.payment_repo.create(
            {
                "order_id": order_id,
                "provider": provider,
                "amount": amount,
                "status": status,
                "payment_url": payment_url,
                "external_id": external_id,
                "raw_payload": raw_payload[:4000],
            }
        )
        await self.payment_repo.session.flush()
        return created

    async def create_payment(self, *, user_id: int, order_id: int, provider: str) -> dict:
        selected = provider.lower().strip()
        if selected not in {item.value for item in PaymentMethod}:
            raise HTTPException(status_code=400, detail="Unsupported provider")

        order = await self.order_repo.get_for_user(order_id=order_id, user_id=user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status not in {OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value}:
            raise HTTPException(status_code=400, detail="Order is not payable")

        existing = await self.payment_repo.get_last_by_order_and_provider(order.id, selected)
        if existing and existing.status in {"pending", "paid", "awaiting_cash", "cash_received"}:
            return {
                "payment_id": existing.id,
                "order_id": order.id,
                "provider": selected,
                "payment_url": existing.payment_url,
                "status": existing.status,
            }

        if selected == PaymentMethod.CLICK.value:
            payment_url = self.generate_click_url(order.id, order.total_amount)
            payment_status = "pending"
        elif selected == PaymentMethod.PAYME.value:
            payment_url = self.generate_payme_url(order.id, order.total_amount)
            payment_status = "pending"
        else:
            payment_url = ""
            payment_status = "awaiting_cash"

        payment = await self.payment_repo.create(
            {
                "order_id": order.id,
                "provider": selected,
                "amount": order.total_amount,
                "status": payment_status,
                "payment_url": payment_url,
            }
        )
        await self.payment_repo.session.flush()
        return {
            "payment_id": payment.id,
            "order_id": order.id,
            "provider": selected,
            "payment_url": payment_url,
            "status": payment.status,
        }

    async def process_click_prepare(self, body_text: str) -> dict:
        data = dict(parse_qsl(body_text, keep_blank_values=True))
        if not self.verify_click_sign(data):
            raise HTTPException(status_code=400, detail="Invalid Click signature")

        order_id = int(data.get("merchant_trans_id") or 0)
        click_trans_id = str(data.get("click_trans_id") or "")
        amount = int(float(data.get("amount") or 0))
        order = await self.order_repo.get(order_id)
        if not order:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": str(order_id),
                "error": -5,
                "error_note": "Order not found",
            }

        await self._upsert_payment(
            provider=PaymentMethod.CLICK.value,
            order_id=order.id,
            amount=amount or order.total_amount,
            status="pending",
            external_id=click_trans_id,
            raw_payload=body_text,
        )
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": str(order.id),
            "error": 0,
            "error_note": "Success",
        }

    async def process_click_complete(self, body_text: str) -> dict:
        data = dict(parse_qsl(body_text, keep_blank_values=True))
        if not self.verify_click_sign(data):
            raise HTTPException(status_code=400, detail="Invalid Click signature")

        order_id = int(data.get("merchant_trans_id") or 0)
        click_trans_id = str(data.get("click_trans_id") or "")
        action = str(data.get("action") or "")
        amount = int(float(data.get("amount") or 0))
        paid = action in {"1", "2"}

        order = await self.order_repo.get(order_id, with_relations=True)
        if not order:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": str(order_id),
                "error": -5,
                "error_note": "Order not found",
                "status": "not_found",
            }

        payment = await self._upsert_payment(
            provider=PaymentMethod.CLICK.value,
            order_id=order.id,
            amount=amount or order.total_amount,
            status="paid" if paid else "failed",
            external_id=click_trans_id,
            raw_payload=body_text,
        )

        if paid:
            order = await self.order_service.update_status(
                order_id=order.id,
                new_status=OrderStatus.CONFIRMED.value,
                changed_by=f"click:{click_trans_id or 'callback'}",
                notes="Click complete callback",
            )
            payment.status = "paid"
        elif order.user and order.user.telegram_user_id:
            await self.notification.notify_user(
                order.user.telegram_user_id,
                t("payment_failed", order.user.language if order.user else "en"),
            )

        await self.payment_repo.session.flush()
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": str(order.id),
            "error": 0,
            "error_note": "Success",
            "status": order.status,
        }

    async def process_payme_rpc(self, method: str, params: dict) -> dict:
        method = (method or "").strip()
        if method == "CheckPerformTransaction":
            return await self.check_perform_transaction(params)
        if method == "CreateTransaction":
            return await self.create_transaction(params)
        if method == "PerformTransaction":
            return await self.perform_transaction(params)
        if method == "CancelTransaction":
            return await self.cancel_transaction(params)
        raise PaymeServiceError(code=-32601, message="Method not found")

    async def _resolve_order_for_payme(self, params: dict):
        account = params.get("account", {}) if isinstance(params, dict) else {}
        order_id = int(account.get("order_id") or 0)
        if not order_id:
            raise PaymeServiceError(code=-31050, message="Order id is required", data="order_id")
        order = await self.order_repo.get(order_id, with_relations=True)
        if not order:
            raise PaymeServiceError(code=-31050, message="Order not found", data="order_id")
        return order

    @staticmethod
    def _extract_amount_tiyin(params: dict) -> int:
        try:
            return int(params.get("amount") or 0)
        except (TypeError, ValueError) as exc:
            raise PaymeServiceError(code=-31001, message="Invalid amount", data="amount") from exc

    async def check_perform_transaction(self, params: dict) -> dict:
        order = await self._resolve_order_for_payme(params)
        amount_tiyin = self._extract_amount_tiyin(params)
        amount_sum = self._amount_sum_from_tiyin(amount_tiyin)
        if amount_sum != order.total_amount:
            raise PaymeServiceError(code=-31001, message="Invalid amount", data="amount")
        if order.status not in {OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value}:
            raise PaymeServiceError(code=-31008, message="Cannot perform transaction", data="status")
        return {"allow": True}

    async def create_transaction(self, params: dict) -> dict:
        transaction_id = str(params.get("id") or "")
        if not transaction_id:
            raise PaymeServiceError(code=-31003, message="Transaction id is required", data="id")
        order = await self._resolve_order_for_payme(params)
        amount_tiyin = self._extract_amount_tiyin(params)
        amount_sum = self._amount_sum_from_tiyin(amount_tiyin)
        if amount_sum != order.total_amount:
            raise PaymeServiceError(code=-31001, message="Invalid amount", data="amount")

        payment = await self._upsert_payment(
            provider=PaymentMethod.PAYME.value,
            order_id=order.id,
            amount=amount_sum,
            status="pending",
            payment_url=self.generate_payme_url(order.id, order.total_amount),
            external_id=transaction_id,
            raw_payload=json.dumps(params, ensure_ascii=False),
        )
        created_ms = int(payment.created_at.timestamp() * 1000) if payment.created_at else self._now_ms()
        return {"create_time": created_ms, "transaction": str(payment.id), "state": 1}

    async def perform_transaction(self, params: dict) -> dict:
        transaction_id = str(params.get("id") or "")
        payment = await self.payment_repo.get_by_external_id(PaymentMethod.PAYME.value, transaction_id)
        if not payment:
            raise PaymeServiceError(code=-31003, message="Transaction not found", data="id")

        order = await self.order_repo.get(payment.order_id, with_relations=True)
        if not order:
            raise PaymeServiceError(code=-31050, message="Order not found", data="order_id")

        payment.status = "paid"
        payment.raw_payload = json.dumps(params, ensure_ascii=False)
        await self.payment_repo.session.flush()

        order = await self.order_service.update_status(
            order_id=order.id,
            new_status=OrderStatus.CONFIRMED.value,
            changed_by=f"payme:{transaction_id or 'rpc'}",
            notes="Payme perform transaction",
        )
        performed_ms = self._now_ms()
        return {"perform_time": performed_ms, "transaction": str(payment.id), "state": 2, "status": order.status}

    async def cancel_transaction(self, params: dict) -> dict:
        transaction_id = str(params.get("id") or "")
        reason = params.get("reason")
        payment = await self.payment_repo.get_by_external_id(PaymentMethod.PAYME.value, transaction_id)
        if not payment:
            raise PaymeServiceError(code=-31003, message="Transaction not found", data="id")

        payment.status = "cancelled"
        payment.raw_payload = json.dumps(params, ensure_ascii=False)
        await self.payment_repo.session.flush()

        order = await self.order_repo.get(payment.order_id, with_relations=True)
        if order and order.status in {OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value}:
            await self.order_service.update_status(
                order_id=order.id,
                new_status=OrderStatus.CANCELLED.value,
                changed_by=f"payme:{transaction_id or 'rpc'}",
                notes=f"Payme cancel transaction reason={reason}",
            )
        cancelled_ms = self._now_ms()
        return {"cancel_time": cancelled_ms, "transaction": str(payment.id), "state": -1}

    async def mark_cash_received(self, order_id: int, *, changed_by: str = "admin:cash") -> dict:
        order = await self.order_repo.get(order_id, with_relations=True)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.payment_method != PaymentMethod.CASH.value:
            raise HTTPException(status_code=400, detail="Order is not cash payment")

        payment = await self.payment_repo.get_last_by_order_and_provider(order_id, PaymentMethod.CASH.value)
        if not payment:
            payment = await self.payment_repo.create(
                {
                    "order_id": order.id,
                    "provider": PaymentMethod.CASH.value,
                    "amount": order.total_amount,
                    "status": "cash_received",
                    "payment_url": "",
                }
            )
        else:
            payment.status = "cash_received"

        order = await self.order_service.update_status(
            order_id=order.id,
            new_status=OrderStatus.CONFIRMED.value,
            changed_by=changed_by,
            notes="Cash received by admin",
        )
        await self.payment_repo.session.flush()
        return {
            "ok": True,
            "order_id": order.id,
            "status": order.status,
            "payment_status": payment.status,
        }

    async def process_callback(self, request: Request, body_text: str, content_type: str) -> dict:
        provider = request.query_params.get("provider", "").lower()
        if not provider and content_type.startswith("application/json"):
            try:
                parsed_json = json.loads(body_text)
                provider = str(parsed_json.get("provider", "")).lower()
            except json.JSONDecodeError:
                provider = ""

        if provider not in {"click", "payme", "internal"}:
            raise HTTPException(status_code=400, detail="Unknown provider")

        if provider == "click":
            return await self.process_click_complete(body_text)

        if provider == "payme":
            if not self.verify_payme_auth(request.headers.get("Authorization", "")):
                raise HTTPException(status_code=401, detail="Invalid Payme auth")
            payload = json.loads(body_text or "{}")
            method = str(payload.get("method") or "")
            params = payload.get("params", {})
            result = await self.process_payme_rpc(method, params)
            # For backward-compatible callback endpoint, return order id/status when present.
            status = str(result.get("status") or "pending")
            order_id = int(params.get("account", {}).get("order_id") or 0)
            return {"ok": True, "order_id": order_id, "status": status}

        callback = PaymentCallbackPayload.model_validate_json(body_text)
        if not validate_internal_callback_signature(
            callback.signature or "",
            body_text,
            settings.click_secret_key or settings.payme_key,
        ):
            raise HTTPException(status_code=401, detail="Invalid callback signature")
        order = await self.order_repo.get(callback.order_id, with_relations=True)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        payment = await self._upsert_payment(
            provider=callback.provider.lower(),
            order_id=order.id,
            amount=callback.amount or order.total_amount,
            status=callback.status.lower(),
            external_id=callback.transaction_id,
            raw_payload=body_text,
        )

        if callback.status.lower() == "paid":
            order = await self.order_service.update_status(
                order_id=order.id,
                new_status=OrderStatus.CONFIRMED.value,
                changed_by=f"{callback.provider}:{callback.transaction_id or 'callback'}",
                notes="Internal payment callback",
            )
            payment.status = "paid"
            await self.payment_repo.session.flush()
        elif order.user and order.user.telegram_user_id:
            await self.notification.notify_user(
                order.user.telegram_user_id,
                t("payment_failed_retry", order.user.language if order.user else "en"),
            )

        return {"ok": True, "order_id": order.id, "status": order.status}
