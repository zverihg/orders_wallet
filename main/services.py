"""
Application services for order and wallet operations.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from django.db import transaction
from django.utils import timezone

from main.domain.order import Order, OrderStatus
from main.domain.wallet import Wallet
from main.domain.events import (
    OrderCreated,
    OrderConfirmed,
    OrderPaid,
    WalletCreated,
    WalletDebited,
    WalletCredited,
)
from main.infra.repositories import (
    CustomerRepository,
    OrderRepository,
    WalletRepository,
)
from main.infra.outbox import OutboxRepository
from main.infra.event_store import EventStoreRepository
from main.infra.locks import wallet_lock
import logging
import json
import time


logger = logging.getLogger(__name__)

class OrderService:
    """Service for order operations."""

    def __init__(
        self,
        order_repo: OrderRepository | None = None,
        wallet_repo: WalletRepository | None = None,
        customer_repo: CustomerRepository | None = None,
        outbox_repo: OutboxRepository | None = None,
        event_store_repo: EventStoreRepository | None = None,
    ):
        self.order_repo = order_repo or OrderRepository()
        self.wallet_repo = wallet_repo or WalletRepository()
        self.customer_repo = customer_repo or CustomerRepository()
        self.outbox_repo = outbox_repo or OutboxRepository()
        self.event_store_repo = event_store_repo or EventStoreRepository()

    @transaction.atomic
    def create_order(
        self,
        customer_id: str,
        items: list[dict],
    ) -> UUID:
        """Create draft order."""
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "services.py:53", "message": "create_order_entry", "data": {"customer_id": customer_id}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        # Validate customer exists
        customer = self.customer_repo.get_by_id(customer_id)
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "services.py:60", "message": "customer_lookup_result", "data": {"customer_found": customer is not None}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # Create order
        order = Order(customer_id=UUID(customer_id))

        # Add items
        for item in items:

            order.add_item(
                product_id=UUID(item["productId"]),
                quantity=int(item["quantity"]),
                price=Decimal(str(item["price"])),
            )

        # Save order (as DRAFT)
        order_id = self.order_repo.save(order)

        # Emit event
        event = OrderCreated(
            event_id=uuid4(),
            aggregate_id=order_id,
            event_type="OrderCreated",
            customer_id=UUID(customer_id),
            total_amount=order.total_amount,
            items_count=len(order.items),
        )
        event.occurred_at = timezone.now().isoformat()

        # Save to event store and outbox
        self.event_store_repo.save_event(event, "Order")

        self.outbox_repo.add_event(event, "Order")
        return order_id

    @transaction.atomic
    def capture_payment(self, order_id: UUID) -> dict:
        """Capture payment for order (debit from wallet, mark as paid)."""
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "services.py:97", "message": "capture_payment_entry", "data": {"order_id": str(order_id)}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        # Get order
        order = self.order_repo.get_by_id(order_id)
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "services.py:100", "message": "order_lookup", "data": {"order_found": order is not None, "order_status": order.status.value if order else "N/A"}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Confirm order if it's still DRAFT
        if order.status == OrderStatus.DRAFT:
            # #region agent log
            try:
                log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "services.py:105", "message": "confirming_draft_order", "data": {}, "timestamp": int(time.time() * 1000)}
                with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except: pass
            # #endregion
            order.confirm()
            self.order_repo.save(order)
            
            # Emit OrderConfirmed event
            event = OrderConfirmed(
                event_id=uuid4(),
                aggregate_id=order_id,
                event_type="OrderConfirmed",
            )
            event.occurred_at = timezone.now().isoformat()
            self.event_store_repo.save_event(event, "Order")
            self.outbox_repo.add_event(event, "Order")
            
            # Reload to get updated status
            order = self.order_repo.get_by_id(order_id)

        if order.status != OrderStatus.PENDING:
            raise ValueError(f"Order {order_id} is not in PENDING status")

        # Get or create wallet
        wallet = self.wallet_repo.get_by_customer_id(order.customer_id)
        if not wallet:
            # Create wallet if doesn't exist
            wallet = Wallet(customer_id=order.customer_id)
            self.wallet_repo.save(wallet)
            
            # Emit WalletCreated event
            event = WalletCreated(
                event_id=uuid4(),
                aggregate_id=wallet.id,
                event_type="WalletCreated",
                customer_id=order.customer_id,
            )
            event.occurred_at = timezone.now().isoformat()
            self.event_store_repo.save_event(event, "Wallet")
            self.outbox_repo.add_event(event, "Wallet")

        # Use distributed lock to prevent double spending
        with wallet_lock(wallet.id):
            # Reload wallet within lock
            wallet = self.wallet_repo.get_by_id(wallet.id)
            
            # Debit from wallet
            debit_transaction = wallet.debit(
                amount=order.total_amount,
                order_id=order.id,
                description=f"Payment for order {order.id}",
            )
            
            # Emit WalletDebited event
            event = WalletDebited(
                event_id=uuid4(),
                aggregate_id=wallet.id,
                event_type="WalletDebited",
                amount=order.total_amount,
                order_id=order.id,
                description=f"Payment for order {order.id}",
                new_balance=wallet.balance,
            )
            event.occurred_at = timezone.now().isoformat()
            self.event_store_repo.save_event(event, "Wallet")
            self.outbox_repo.add_event(event, "Wallet")

            # Calculate bonus (5% of order amount)
            bonus_amount = order.total_amount * Decimal("0.05")

            # Credit bonus
            credit_transaction = wallet.credit(
                amount=bonus_amount,
                order_id=order.id,
                description=f"Bonus for order {order.id}",
            )
            
            # Emit WalletCredited event
            event = WalletCredited(
                event_id=uuid4(),
                aggregate_id=wallet.id,
                event_type="WalletCredited",
                amount=bonus_amount,
                order_id=order.id,
                description=f"Bonus for order {order.id}",
                new_balance=wallet.balance,
            )
            event.occurred_at = timezone.now().isoformat()
            self.event_store_repo.save_event(event, "Wallet")
            self.outbox_repo.add_event(event, "Wallet")

            # Mark order as paid
            order.mark_paid()

            # Save wallet and order
            self.wallet_repo.save(wallet)
            self.order_repo.save(order)
            
            # Emit OrderPaid event
            event = OrderPaid(
                event_id=uuid4(),
                aggregate_id=order_id,
                event_type="OrderPaid",
                amount=order.total_amount,
            )
            event.occurred_at = timezone.now().isoformat()
            self.event_store_repo.save_event(event, "Order")
            self.outbox_repo.add_event(event, "Order")

        return {
            "order_id": order.id,
            "status": order.status.value,
            "amount_debited": order.total_amount,
            "bonus_credited": bonus_amount,
        }

    def get_order(self, order_id: UUID) -> Order | None:
        """Get order by ID."""
        return self.order_repo.get_by_id(order_id)

    def get_orders_by_customer(self, customer_id: UUID, limit: int = 50, offset: int = 0) -> list[Order]:
        """Get orders by customer with pagination."""
        return self.order_repo.get_by_customer(customer_id, limit=limit, offset=offset)


class WalletService:
    """Service for wallet operations."""

    def __init__(
        self,
        wallet_repo: WalletRepository | None = None,
        customer_repo: CustomerRepository | None = None,
    ):
        self.wallet_repo = wallet_repo or WalletRepository()
        self.customer_repo = customer_repo or CustomerRepository()

    def get_balance(self, customer_id: str) -> dict:
        """Get wallet balance for customer."""
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H3", "location": "services.py:238", "message": "get_balance_entry", "data": {"customer_id": customer_id}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        # Validate customer exists
        customer = self.customer_repo.get_by_id(customer_id)
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H3", "location": "services.py:241", "message": "customer_lookup_balance", "data": {"customer_found": customer is not None}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        wallet = customer.wallet
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H3", "location": "services.py:246", "message": "wallet_lookup", "data": {"wallet_found": wallet is not None}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        if not wallet:
            return {
                "customerId": customer_id,
                "balance": Decimal("0.00"),
            }

        balance = self.wallet_repo.get_balance_wallet(wallet)
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H3", "location": "services.py:254", "message": "balance_calculated", "data": {"balance": str(balance)}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        return {
            "customerId": customer_id,
            "balance": balance,
        }

