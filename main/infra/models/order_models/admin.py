from django.contrib import admin
from django.contrib.admin import ModelAdmin

from main.infra.models.order_models.models import Order, OrderItem


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_id",
        "quantity",
        "price",
    )


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("id", "customer", "status", "total_amount")
