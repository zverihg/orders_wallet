from decimal import Decimal

from django.db import migrations, models


def sanitize_wallet_transactions(apps, schema_editor):
    WalletTransaction = apps.get_model("wallet_models", "WalletTransaction")

    WalletTransaction.objects.filter(amount__lt=0).update(amount=Decimal("0.01"))
    WalletTransaction.objects.filter(amount=0).update(amount=Decimal("0.01"))


class Migration(migrations.Migration):
    dependencies = [
        ("wallet_models", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sanitize_wallet_transactions, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="wallettransaction",
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="wallet_tx_amount_gt_0",
            ),
        ),
    ]

