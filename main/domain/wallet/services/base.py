from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from main.domain.errors import DomainError
from main.infra.models.wallet_models.models import TransactionType, Wallet, WalletTransaction


class BaseWalletService:
    def _get_wallet(self, customer_id: UUID) -> Wallet:
        try:
            return Wallet.objects.prefetch_related("transactions").get(customer_id=customer_id)
        except Wallet.DoesNotExist as exc:
            raise DomainError(code="WALLET_NOT_FOUND", message="Wallet not found") from exc

    def _to_transaction_type_value(self, operation_type: str) -> str:
        try:
            return TransactionType(operation_type).value
        except ValueError as exc:
            raise DomainError(code="UNSUPPORTED_WALLET_OPERATION", message="Unsupported wallet operation") from exc

    def _balance_from_wallet(self, wallet: Wallet) -> Decimal:
        balance = Decimal("0.00")
        for transaction in wallet.transactions.all():
            tx_type = transaction.transaction_type
            if tx_type in (TransactionType.CREDIT, TransactionType.CREDIT.value):
                balance += transaction.amount
            elif tx_type in (TransactionType.DEBIT, TransactionType.DEBIT.value):
                balance -= transaction.amount
        return balance

    def _create_transaction(
        self,
        *,
        wallet: Wallet,
        operation_type: str,
        amount: Decimal,
        description: str = "",
    ) -> WalletTransaction:
        if amount <= Decimal("0"):
            raise DomainError(code="INVALID_AMOUNT", message="Amount must be greater than zero")
        transaction_type = self._to_transaction_type_value(operation_type)
        return WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
        )
