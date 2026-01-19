"""
Infrastructure repositories for domain entities.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.db import transaction

from main.domain.order import Order, OrderItem, OrderStatus
from main.domain.wallet import Wallet, WalletTransaction, TransactionType
from main.infra.models import (
    CustomerORM,
    OrderORM,
    OrderItemORM,
    WalletORM,
    WalletTransactionORM,
)
from main.infra.event_store import EventStoreRepository
import logging
import json
import time
logger = logging.getLogger(__name__)


class CustomerRepository:
    """Repository for Customer entities."""

    def get_by_id(self, customer_id: str) -> CustomerORM | None:
        """Get customer by ID."""
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "repositories.py:28", "message": "customer_get_by_id_entry", "data": {"customer_id": customer_id}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        result = CustomerORM.objects.filter(id=customer_id).first()
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "repositories.py:30", "message": "customer_get_by_id_result", "data": {"customer_found": result is not None, "customer_id": customer_id}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        return result

    def create(self, name: str) -> UUID:
        """Create new customer."""
        new_customer = CustomerORM.objects.create(
            name=name,
        )
        return new_customer.id


class OrderRepository:
    """Repository for Order aggregate."""

    def get_by_id(self, order_id: UUID) -> Order | None:
        """Get order by ID with items (optimized, no N+1)."""
        try:
            order_orm = (
                OrderORM.objects
                .select_related("customer")
                .prefetch_related("items")
                .get(id=order_id)
            )
            return self._to_domain(order_orm)
        except OrderORM.DoesNotExist:
            return None

    def get_by_customer(self, customer_id: UUID, limit: int = 50, offset: int = 0) -> list[Order]:
        """Get orders by customer with pagination (optimized)."""
        orders_orm = (
            OrderORM.objects
            .filter(customer_id=customer_id)
            .select_related("customer")
            .prefetch_related("items")
            .order_by("-created_at")[offset:offset + limit]
        )
        return [self._to_domain(order_orm) for order_orm in orders_orm]

    @transaction.atomic
    def save(self, order: Order) -> UUID:
        """Save order aggregate."""
        order_orm, created = OrderORM.objects.update_or_create(
            id=order.id,
            defaults={
                "customer_id": order.customer_id,
                "total_amount": order.total_amount,
                "status": order.status.value,
            }
        )

        # Delete existing items and recreate
        if not created:
            OrderItemORM.objects.filter(order=order_orm).delete()

        # Create items
        for item in order.items:
            OrderItemORM.objects.create(
                order=order_orm,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price,
            )

        return order_orm.id

    def _to_domain(self, order_orm: OrderORM) -> Order:
        """Convert ORM model to domain entity."""
        # Build items list directly (bypass add_item() validation for loading from DB)
        items = []
        for item_orm in order_orm.items.all():
            items.append(OrderItem(
                product_id=item_orm.product_id,
                quantity=item_orm.quantity,
                price=item_orm.price,
            ))
        
        order = Order(
            id=order_orm.id,
            customer_id=order_orm.customer_id,
            items=items,
            status=OrderStatus(order_orm.status),
        )
        
        return order


class WalletRepository:
    """Repository for Wallet aggregate."""

    def __init__(self, event_store_repo: EventStoreRepository | None = None):
        self.event_store_repo = event_store_repo or EventStoreRepository()

    def get_by_customer_id(self, customer_id: UUID) -> Wallet | None:
        """Get wallet by customer ID with transactions (optimized)."""
        try:
            wallet_orm = (
                WalletORM.objects
                .select_related("customer")
                .prefetch_related("transactions")
                .get(customer_id=customer_id)
            )
            return self._to_domain(wallet_orm)
        except WalletORM.DoesNotExist:
            return None


    def get_by_customer(self, customer_id: UUID) -> Wallet | None:
        """Get wallet by customer ID with transactions (optimized)."""
        try:
            wallet_orm = (
                WalletORM.objects
                .select_related("customer")
                .prefetch_related("transactions")
                .get(customer_id=customer_id)
            )
            return self._to_domain(wallet_orm)
        except WalletORM.DoesNotExist:
            return None


    def get_by_id(self, wallet_id: UUID) -> Wallet | None:
        """Get wallet by ID."""
        try:
            wallet_orm = (
                WalletORM.objects
                .select_related("customer")
                .prefetch_related("transactions")
                .get(id=wallet_id)
            )
            return self._to_domain(wallet_orm)
        except WalletORM.DoesNotExist:
            return None

    def get_balance_wallet(self, wallet: WalletORM):
        balance = self.event_store_repo.calculate_wallet_balance(wallet)
        return balance


    @transaction.atomic
    def save(self, wallet: Wallet) -> UUID:
        """Save wallet aggregate with invariant validation."""
        # Validate balance is non-negative
        if wallet.balance < 0:
            raise ValueError(f"Wallet balance cannot be negative: {wallet.balance}")

        # Validate balance matches transactions
        calculated_balance = wallet.calculate_balance_from_transactions()
        if abs(wallet.balance - calculated_balance) > Decimal("0.01"):  # Allow small rounding differences
            raise ValueError(
                f"Wallet balance {wallet.balance} does not match "
                f"calculated balance {calculated_balance}"
            )

        # Save wallet (without balance - it's calculated from events)
        wallet_orm, created = WalletORM.objects.update_or_create(
            id=wallet.id,
            defaults={
                "customer_id": wallet.customer_id,
            }
        )

        # Save new transactions (transactions are immutable - only add new ones)
        existing_transaction_ids = set(
            WalletTransactionORM.objects
            .filter(wallet=wallet_orm)
            .values_list("id", flat=True)
        )

        for transaction in wallet.transactions:
            if transaction.id not in existing_transaction_ids:
                WalletTransactionORM.objects.create(
                    id=transaction.id,
                    wallet=wallet_orm,
                    transaction_type=transaction.transaction_type.value,
                    amount=transaction.amount,
                    order_id=transaction.order_id,
                    description=transaction.description,
                )

        return wallet_orm.id

    def _to_domain(self, wallet_orm: WalletORM) -> Wallet:
        """Convert ORM model to domain entity."""
        # Calculate balance from events
        balance = self.event_store_repo.calculate_wallet_balance(wallet_orm)
        
        wallet = Wallet(
            id=wallet_orm.id,
            customer_id=wallet_orm.customer_id,
            balance=balance,
        )

        # Add transactions
        for trans_orm in wallet_orm.transactions.all():
            transaction = WalletTransaction(
                id=trans_orm.id,
                wallet_id=wallet_orm.id,
                transaction_type=TransactionType(trans_orm.transaction_type),
                amount=trans_orm.amount,
                order_id=trans_orm.order_id,
                description=trans_orm.description,
            )
            wallet._transactions.append(transaction)

        return wallet
