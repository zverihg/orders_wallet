from django.contrib import admin


from main.infra.models.customer_models.models import Customer
from main.infra.models.order_models.models import Order, OrderItem
from main.infra.models.wallet_models.models import Payment, Wallet, WalletTransaction
from main.infra.models.service_models.models.idempotency_key import IdempotencyKey

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "customer__name")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product_id", "quantity", "price", "created_at")
    list_filter = ("created_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "pay_type", "created_at")
    list_filter = ("pay_type", "created_at")


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "created_at")
    search_fields = ("customer__name",)
    readonly_fields = ("id", "customer")
    
    def get_queryset(self, request):
        """Add calculated balance to queryset."""
        qs = super().get_queryset(request)
        # Balance is calculated from events, not stored
        return qs


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "wallet", "transaction_type", "amount", "order_id", "created_at")
    list_filter = ("transaction_type", "created_at")


@admin.register(IdempotencyKey)
class IdempotencyAdmin(admin.ModelAdmin):
    list_display = ("key", "user_id", "operation", "created_at")
    list_filter = ("operation", "created_at")
    search_fields = ("key", "user_id")

