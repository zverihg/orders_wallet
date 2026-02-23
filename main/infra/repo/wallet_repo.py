from decimal import Decimal
from uuid import UUID

from django.db.transaction import atomic

from main.infra.models.order_models.models import Order

from main.infra.models.wallet_models.models import Wallet, WalletTransaction, TransactionType

class WalletRepo:

    def get_wallet_balance(self, customer_id: UUID) -> Decimal:

        wallet = Wallet.objects.get(customer=customer_id)

        balance = Decimal(0)
        for wallet_transaction in wallet.transactions.all():
            if wallet_transaction.transaction_type == TransactionType.CREDIT:
                balance += wallet_transaction.amount
            elif wallet_transaction.transaction_type == TransactionType.DEBIT:
                balance -= wallet_transaction.amount
            else:
                pass

        return balance

    @atomic
    def capture_payment(self, order_id: UUID) -> str:

        order = Order.objects.get(order_id=order_id)

        wallet = order.customer.wallet

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=TransactionType.DEBIT,
            amount=order.total_amount,
            description=f"Payment for order {order.id}",
        )

        order.status = "PAID"
        order.save()

        return order.status

    @atomic
    def refund_order(self, order_id: str):

        order = Order.objects.get(order_id=order_id)

        wallet = order.customer.wallet

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=TransactionType.CREDIT,
            amount=order.total_amount,
            description=f"Payment for order {order.id}",
        )

        order.status = "REFUNDED"
        order.save()

    def _wallet_proccess(self, operation_type: TransactionType, amount: Decimal, customer_id: str):
        wallet = Wallet.objects.get(customer_id=customer_id)
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=operation_type,
            amount=amount,
        )

        return True

    def wallet_debit(self, customer_id: str, amount: Decimal):

        self._wallet_proccess(
            operation_type=TransactionType.DEBIT,
            amount=amount,
            customer_id=customer_id,
        )

        result = {"status": "success"}

        return result

    def wallet_credit(self, customer_id: str, amount: Decimal):

        self._wallet_proccess(
            operation_type=TransactionType.CREDIT,
            amount=amount,
            customer_id=customer_id,
        )

        result = {"status": "success"}

        return result


wallet_repo = WalletRepo()