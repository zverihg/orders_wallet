from __future__ import annotations

from uuid import UUID

from .base import BaseWalletService


class WalletQueryService(BaseWalletService):
    def get_wallet_balance(self, customer_id: UUID):
        wallet = self._get_wallet(customer_id=customer_id)
        return self._balance_from_wallet(wallet)
