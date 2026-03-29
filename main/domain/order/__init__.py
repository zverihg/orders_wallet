from uuid import UUID

from .services import OrderCommandService, OrderPaymentService, OrderQueryService

_query_service = OrderQueryService()
_command_service = OrderCommandService()
_payment_service = OrderPaymentService()


def create_order(customer_id: UUID, items_list):
    return _command_service.create_order(customer_id=customer_id, items_list=items_list)


def get_order_by_id(order_id: UUID):
    return _query_service.get_order_by_id(order_id=order_id)


def get_orders_by_customer(customer_id: UUID, *, limit: int = 50, offset: int = 0):
    return _query_service.get_orders_by_customer(
        customer_id=customer_id, limit=limit, offset=offset
    )


def capture_payment(order_id: UUID, idempotency_key: str | None = None):
    return _payment_service.capture_payment(
        order_id=order_id, idempotency_key=idempotency_key
    )


def refund_order(order_id: UUID):
    return _payment_service.refund_order(order_id=order_id)


__all__ = [
    "create_order",
    "get_order_by_id",
    "get_orders_by_customer",
    "capture_payment",
    "refund_order",
]
