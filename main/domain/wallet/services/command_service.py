from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.db import transaction

from main.domain.errors import DomainError
from main.domain.idempotency import run_idempotent
from main.infra.models.wallet_models.models import TransactionType, Wallet

from .base import BaseWalletService


class WalletCommandService(BaseWalletService):
    @transaction.atomic
    def wallet_debit(
        self, customer_id: UUID, amount: Decimal, idempotency_key: str | None = None
    ) -> dict:
        def _debit():
            wallet = (
                Wallet.objects.select_for_update()
                .prefetch_related("transactions")
                .filter(customer_id=customer_id)
                .first()
            )
            if not wallet:
                raise DomainError(code="WALLET_NOT_FOUND", message="Wallet not found")

            current_balance = self._balance_from_wallet(wallet)
            if amount > current_balance:
                raise DomainError(
                    code="WALLET_INSUFFICIENT_BALANCE",
                    message="Insufficient wallet balance",
                )
            self._create_transaction(
                wallet=wallet,
                operation_type=TransactionType.DEBIT.value,
                amount=amount,
                description="Manual wallet debit",
            )
            return {"status": "success"}

        return run_idempotent(
            operation="WALLET_DEBIT",
            key=idempotency_key,
            user_id=customer_id,
            payload={"customerId": str(customer_id), "amount": str(amount)},
            handler=_debit,
        )

    @transaction.atomic
    def wallet_credit(self, customer_id: UUID, amount: Decimal) -> dict:
        wallet = self._get_wallet(customer_id=customer_id)
        self._create_transaction(
            wallet=wallet,
            operation_type=TransactionType.CREDIT.value,
            amount=amount,
            description="Manual wallet credit",
        )
        return {"status": "success"}
