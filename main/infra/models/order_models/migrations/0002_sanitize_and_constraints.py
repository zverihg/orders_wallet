from decimal import Decimal

from django.db import migrations, models


def sanitize_order_data(apps, schema_editor):
    Order = apps.get_model("order_models", "Order")
    OrderItem = apps.get_model("order_models", "OrderItem")

    Order.objects.filter(total_amount__lt=0).update(total_amount=Decimal("0.00"))
    OrderItem.objects.filter(quantity__lte=0).update(quantity=1)
    OrderItem.objects.filter(price__lt=0).update(price=Decimal("0.00"))


class Migration(migrations.Migration):
    dependencies = [
        ("order_models", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sanitize_order_data, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="order_total_amount_gte_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="order_item_quantity_gt_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="order_item_price_gte_0",
            ),
        ),
    ]

