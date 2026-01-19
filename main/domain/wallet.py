"""
Domain model for Wallet aggregate.
"""
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class TransactionType(str, Enum):
    """Wallet transaction type."""
    DEBIT = "DEBIT"  # Списание
    CREDIT = "CREDIT"  # Начисление


class WalletTransaction:
    """Immutable wallet transaction value object."""
    
    def __init__(
        self,
        id: UUID,
        wallet_id: UUID,
        transaction_type: TransactionType,
        amount: Decimal,
        order_id: UUID | None = None,
        description: str = "",
    ):
        if amount <= 0:
            raise ValueError("Transaction amount must be positive")
        
        self.id = id
        self.wallet_id = wallet_id
        self.transaction_type = transaction_type
        self.amount = amount
        self.order_id = order_id
        self.description = description


class Wallet:
    """Wallet aggregate root."""
    
    def __init__(
        self,
        id: UUID | None = None,
        customer_id: UUID | None = None,
        balance: Decimal = Decimal("0.00"),
        transactions: list[WalletTransaction] | None = None,
    ):
        self.id = id or uuid4()
        self.customer_id = customer_id
        self._balance = balance
        self._transactions = transactions or []
    
    @property
    def balance(self) -> Decimal:
        """Get current wallet balance."""
        return self._balance
    
    @property
    def transactions(self) -> list[WalletTransaction]:
        """Get wallet transactions (immutable)."""
        return list(self._transactions)
    
    def debit(self, amount: Decimal, order_id: UUID | None = None, description: str = "") -> WalletTransaction:
        """Debit (withdraw) from wallet."""
        if amount <= 0:
            raise ValueError("Debit amount must be positive")
        
        if self._balance < amount:
            raise ValueError(f"Insufficient balance. Available: {self._balance}, requested: {amount}")
        
        transaction = WalletTransaction(
            id=uuid4(),
            wallet_id=self.id,
            transaction_type=TransactionType.DEBIT,
            amount=amount,
            order_id=order_id,
            description=description,
        )
        
        self._balance -= amount
        self._transactions.append(transaction)
        
        return transaction
    
    def credit(self, amount: Decimal, order_id: UUID | None = None, description: str = "") -> WalletTransaction:
        """Credit (deposit) to wallet."""
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        
        transaction = WalletTransaction(
            id=uuid4(),
            wallet_id=self.id,
            transaction_type=TransactionType.CREDIT,
            amount=amount,
            order_id=order_id,
            description=description,
        )
        
        self._balance += amount
        self._transactions.append(transaction)
        
        return transaction
    
    def calculate_balance_from_transactions(self) -> Decimal:
        """Calculate balance from all transactions (for validation)."""
        balance = Decimal("0.00")
        for transaction in self._transactions:
            if transaction.transaction_type == TransactionType.CREDIT:
                balance += transaction.amount
            else:
                balance -= transaction.amount
        return balance

