from __future__ import annotations

from ariadne import MutationType

from main.domain.wallet import wallet_credit, wallet_debit

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


@mutation.field("walletDebit")
def resolve_wallet_debit(_, info, input: dict):
    idempotency_key = _idempotency_key_from_context(info)
    return run_with_hybrid_errors(
        lambda: wallet_debit(
            input["customerId"],
            input["amount"],
            idempotency_key=idempotency_key,
        ),
        on_domain_error=lambda exc: domain_error_payload(
            status="ERROR",
            error=exc,
        ),
    )


@mutation.field("walletCredit")
def resolve_wallet_credit(_, info, input: dict):
    return run_with_hybrid_errors(
        lambda: wallet_credit(input["customerId"], input["amount"]),
        on_domain_error=lambda exc: domain_error_payload(
            status="ERROR",
            error=exc,
        ),
    )
