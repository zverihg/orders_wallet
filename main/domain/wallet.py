"""
Доменная модель агрегата Кошелёк (Wallet).
"""
from __future__ import annotations

from decimal import Decimal

from main.infra.repo import wallet_repo

def get_wallet_balance(customer_id: str):

    balance = wallet_repo.get_wallet_balance(customer_id)
    return balance

def wallet_debit(customer_id: str, amount: Decimal):

    result = wallet_repo.wallet_debit(
        customer_id=customer_id,
        amount=amount,
    )
    return result

def wallet_credit(customer_id: str, amount: Decimal):

    result = wallet_repo.wallet_credit(
        customer_id=customer_id,
        amount=amount,
 )
    return result
