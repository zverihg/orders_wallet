from __future__ import annotations

from uuid import UUID

from main.infra.models.order_models.models import Order

from .base import BaseOrderService


class OrderQueryService(BaseOrderService):
    def get_order_by_id(self, order_id: UUID) -> dict:
        order = (
            Order.objects.select_related("customer")
            .prefetch_related("items")
            .filter(id=order_id)
            .first()
        )
        if not order:
            return None
        return self._serialize_order(order)

    def get_orders_by_customer(
        self, customer_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> dict:
        limit = max(1, min(int(limit), 100))
        offset = max(0, int(offset))
        orders_queryset = (
            Order.objects.select_related("customer")
            .prefetch_related("items")
            .filter(customer_id=customer_id)
            .order_by("-created_at")
        )
        total_count = orders_queryset.count()
        page_queryset = orders_queryset[offset : offset + limit]
        orders = [self._serialize_order(order) for order in page_queryset]
        return {
            "orders": orders,
            "totalCount": total_count,
            "limit": limit,
            "offset": offset,
            "hasNextPage": offset + len(orders) < total_count,
        }
