from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from ariadne import MutationType

from main.domain.order import capture_payment, create_order, refund_order

from ..errors import domain_error_payload, run_with_hybrid_errors

mutation = MutationType()


def _idempotency_key_from_context(info) -> str | None:
    context = getattr(info, "context", None)
    if isinstance(context, dict):
        request = context.get("request")
    else:
        request = context
    if request is None or not hasattr(request, "headers"):
        return None
    return request.headers.get("Idempotency-Key")


@mutation.field("createOrder")
def resolve_create_order(_, info, input: dict):
    customer_id_raw = input["customerId"]
    customer_id = customer_id_raw if isinstance(customer_id_raw, UUID) else UUID(str(customer_id_raw))
    items_input = input["items"]
    items_list = [
        {
            "productId": item["productId"] if isinstance(item["productId"], UUID) else UUID(str(item["productId"])),
            "quantity": item["quantity"],
            "price": Decimal(str(item["price"])),
        }
        for item in items_input
    ]
    return run_with_hybrid_errors(
        lambda: create_order(customer_id, items_list),
        on_domain_error=lambda exc: domain_error_payload(
            status="ERROR",
            error=exc,
            orderId=None,
        ),
    )


@mutation.field("capturePayment")
def resolve_capture_payment(_, info, orderId: UUID):
    idempotency_key = _idempotency_key_from_context(info)
    return run_with_hybrid_errors(
        lambda: capture_payment(orderId, idempotency_key=idempotency_key),
        on_domain_error=lambda exc: domain_error_payload(
            status="ERROR",
            error=exc,
            orderId=orderId,
            amountDebited=None,
        ),
    )


@mutation.field("refundOrder")
def resolve_refund_order(_, info, orderId: UUID):
    return run_with_hybrid_errors(
        lambda: refund_order(orderId),
        on_domain_error=lambda exc: domain_error_payload(
            status="ERROR",
            error=exc,
            orderId=orderId,
            amountRefunded=None,
        ),
    )
