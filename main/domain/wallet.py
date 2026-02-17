"""
Domain model for Wallet aggregate.
"""
from __future__ import annotations

from decimal import Decimal
from enum import Enum

from main.infra.models.wallet_models.models import Wallet, WalletTransaction

class TransactionType(str, Enum):
    """Wallet transaction type."""
    DEBIT = "DEBIT"  # Списание
    CREDIT = "CREDIT"  # Начисление

def get_wallet_balance(customer_id: str):

    wallet = Wallet.objects.get(customer_id=customer_id)
    balance = Decimal(0)
    for transaction in wallet.transactions.all():
        if transaction.transaction_type == TransactionType.CREDIT:
            balance += transaction.amount
        elif transaction.transaction_type == TransactionType.DEBIT:
            balance -= transaction.amount
        else:
            pass

    return balance

def wallet_proccess(operation_type: TransactionType, amount: Decimal, customer_id: str):
    wallet = Wallet.objects.get(customer_id=customer_id)
    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=operation_type,
        amount=amount,
    )

    return True

def wallet_debit(customer_id: str, amount: Decimal):

    result_operation = wallet_proccess(
        operation_type =TransactionType.DEBIT,
        customer_id=customer_id,
        amount=amount
    )

    result = {"status": "success"}

    return result

def wallet_credit(customer_id: str, amount: Decimal):
    result_operation = wallet_proccess(
        operation_type=TransactionType.CREDIT,
        customer_id=customer_id,
        amount=amount
    )

    result = {"status": "success"}

    return result