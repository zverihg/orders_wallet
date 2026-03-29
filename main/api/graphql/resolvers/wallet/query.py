from __future__ import annotations

from uuid import UUID

from ariadne import QueryType

from main.domain.wallet import get_wallet_balance

from ..errors import run_with_hybrid_errors

query = QueryType()


@query.field("walletBalance")
def resolve_wallet_balance(_, info, customerId: UUID):
    return run_with_hybrid_errors(
        lambda: {"customerId": customerId, "balance": get_wallet_balance(customerId)},
        on_domain_error=lambda exc: {
            "customerId": customerId,
            "balance": None,
            "errorCode": exc.code,
            "errorMessage": exc.message,
        },
    )
