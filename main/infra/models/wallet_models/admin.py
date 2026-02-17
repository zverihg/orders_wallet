from django.contrib import admin
from django.contrib.admin import ModelAdmin

from main.infra.models.wallet_models.models import Wallet, WalletTransaction


@admin.register(WalletTransaction)
class WalletTransactionAdmin(ModelAdmin):

    list_display = (
        'id',
        'wallet',
        'transaction_type',
        'amount',
        'description',
    )


@admin.register(Wallet)
class WalletAdmin(ModelAdmin):

    list_display = (
        'id',
        'customer',
    )
