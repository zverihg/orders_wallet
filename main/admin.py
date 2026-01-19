from django.contrib import admin

from main.infra.models import (
    OrderORM,
    OrderItemORM,
    PaymentORM,
    IdempotencyKey,
    CustomerORM,
    WalletORM,
    WalletTransactionORM,
)
from main.infra.read_models import OrderSummary, WalletView
from main.infra.event_store import EventStore
from main.infra.outbox import OutboxEvent


@admin.register(CustomerORM)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(OrderORM)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "customer__name")


@admin.register(OrderItemORM)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product_id", "quantity", "price", "created_at")
    list_filter = ("created_at",)


@admin.register(PaymentORM)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "pay_type", "created_at")
    list_filter = ("pay_type", "created_at")


@admin.register(WalletORM)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "created_at")
    search_fields = ("customer__name",)
    readonly_fields = ("id", "customer")
    
    def get_queryset(self, request):
        """Add calculated balance to queryset."""
        qs = super().get_queryset(request)
        # Balance is calculated from events, not stored
        return qs


@admin.register(WalletTransactionORM)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "wallet", "transaction_type", "amount", "order_id", "created_at")
    list_filter = ("transaction_type", "created_at")


@admin.register(IdempotencyKey)
class IdempotencyAdmin(admin.ModelAdmin):
    list_display = ("key", "user_id", "operation", "created_at")
    list_filter = ("operation", "created_at")
    search_fields = ("key", "user_id")


@admin.register(OrderSummary)
class OrderSummaryAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "status", "total_amount", "items_count", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = ("id", "customer_id", "customer_name", "status", "total_amount", "items_count", "created_at_read")


@admin.register(WalletView)
class WalletViewAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_id", "balance", "transactions_count", "last_transaction_at")
    readonly_fields = ("id", "customer_id", "balance", "transactions_count", "last_transaction_at")


@admin.register(EventStore)
class EventStoreAdmin(admin.ModelAdmin):
    list_display = ("id", "aggregate_id", "aggregate_type", "event_type", "sequence_number", "created_at")
    list_filter = ("aggregate_type", "event_type", "created_at")
    readonly_fields = ("id", "aggregate_id", "aggregate_type", "event_type", "event_version", "event_data", "sequence_number")


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = ("id", "aggregate_id", "aggregate_type", "event_type", "processed", "retry_count", "created_at")
    list_filter = ("processed", "aggregate_type", "event_type", "created_at")
    readonly_fields = ("id", "aggregate_id", "aggregate_type", "event_type", "event_data", "processed", "processed_at", "retry_count")

