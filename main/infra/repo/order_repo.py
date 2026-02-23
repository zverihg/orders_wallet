from decimal import Decimal
from uuid import UUID


from django.db.transaction import atomic

from main.infra.models.order_models.models import Order, OrderStatus, OrderItem
from main.infra.models.customer_models.models import Customer
from main.infra.repo.value_objects import (
    CustomerObject,
    OrderItemObject,
    OrderObject,
    OrderObjectPreView
)

class OrderRepo:

    def get_order_by_id(self, order_id: UUID) -> dict:

        order = Order.objects.get(id=order_id)

        customer_obj = CustomerObject(
            id=order.customer.pk,
            name=order.customer.name,
        )

        items = []

        for item in order.items.all():
            items.append(
                OrderItemObject(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                )
            )

        order_object = OrderObject(
            total_amount=order.total_amount,
            status=order.status,
            items=items,
            customer=customer_obj,
        )

        return order_object.__dict__

    def get_orders_by_customer(self, customer_id: UUID) -> list[dict]:

        customer = Customer.objects.get(id=customer_id)

        order_object_list = []

        for order in customer.orders.all():
            order_object_list.append(
                OrderObjectPreView(
                    total_amount=order.total_amount,
                    status=order.status,
                ).__dict__
            )

        return order_object_list

    @atomic
    def create_order(self, order_object: OrderObject):

        customer = Customer.objects.get(id=order_object.customer.id)

        order = Order.objects.create(
            customer=customer,
            total_amount=order_object.total_amount,
            status=OrderStatus.DRAFT,
        )

        for item in order_object.items:

            OrderItem.objects.create(
                order=order,
                product_id=item["productId"],
                quantity=item["quantity"],
                price=item["price"],
            )

        return order.pk, order.status

    def get_order_item_by_id(self, order_item_id: int) -> OrderObject:

        order = Order.objects.get(id=order_item_id)
        items = []
        customer_obj = CustomerObject(
            id=order.customer.pk,
            name=order.customer.name,
        )
        for item in order.items.all():
            items.append(
                OrderItemObject(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                )
            )

        order_object = OrderObject(
            total_amount=order.total_amount,
            status=order.status,
            items=items,
            customer=customer_obj,
        )

        return order_object.__dict__

    def create_order_item(self, product_id: UUID, quantity:int, price:Decimal) -> dict:

        obj = OrderItem.objects.create(
            product_id=product_id,
            quantity=quantity,
            price=price,
        )

        return obj.__dict__





order_repo = OrderRepo()