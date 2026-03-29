"""
Доменная модель агрегата Кошелёк (Wallet).
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from .services import WalletCommandService, WalletQueryService

_wallet_query_service = WalletQueryService()
_wallet_command_service = WalletCommandService()


def get_wallet_balance(customer_id: UUID):
    return _wallet_query_service.get_wallet_balance(customer_id=customer_id)


def wallet_debit(customer_id: UUID, amount: Decimal, idempotency_key: str | None = None):
    return _wallet_command_service.wallet_debit(
        customer_id=customer_id,
        amount=amount,
        idempotency_key=idempotency_key,
    )


def wallet_credit(customer_id: UUID, amount: Decimal):
    return _wallet_command_service.wallet_credit(
        customer_id=customer_id,
        amount=amount,
    )
