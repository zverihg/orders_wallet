from django.contrib import admin

from main.infra.models.customer_models.models import Customer
from main.infra.models.order_models.models import Order, OrderItem
from main.infra.models.wallet_models.models import Payment, Wallet, WalletTransaction
from main.infra.models.service_models.models.idempotency_key import IdempotencyKey

admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Wallet)
admin.site.register(WalletTransaction)
admin.site.register(IdempotencyKey)
