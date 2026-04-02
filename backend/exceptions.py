# -*- coding: utf-8 -*-


class AppException(Exception):
    def __init__(self, message: str, *, code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class OrderNotFound(AppException):
    def __init__(self, message: str = "Order not found") -> None:
        super().__init__(message, code=404)


class PaymentFailed(AppException):
    def __init__(self, message: str = "Payment failed") -> None:
        super().__init__(message, code=400)


class CartEmpty(AppException):
    def __init__(self, message: str = "Cart is empty") -> None:
        super().__init__(message, code=400)


class ProductUnavailable(AppException):
    def __init__(self, message: str = "Product is unavailable") -> None:
        super().__init__(message, code=400)


class InvalidPromoCode(AppException):
    def __init__(self, message: str = "Invalid promo code") -> None:
        super().__init__(message, code=400)
