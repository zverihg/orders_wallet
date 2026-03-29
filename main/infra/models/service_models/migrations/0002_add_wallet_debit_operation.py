from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("service_models", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="idempotencykey",
            name="operation",
            field=models.CharField(
                choices=[
                    ("CREATE_ORDER", "Создание заказа"),
                    ("CAPTURE_PAYMENT", "Подтверждение оплаты"),
                    ("REFUND_ORDER", "Возврат заказа"),
                    ("WALLET_DEBIT", "Списание кошелька"),
                ]
            ),
        ),
    ]

