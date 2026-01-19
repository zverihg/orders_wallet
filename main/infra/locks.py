"""
Distributed locks using PostgreSQL advisory locks.
"""
from contextlib import contextmanager
from uuid import UUID

from django.db import connection, transaction


@contextmanager
def wallet_lock(wallet_id: UUID):
    """
    Acquire advisory lock on wallet for concurrent operations.
    
    Usage:
        with wallet_lock(wallet_id):
            # Perform wallet operations
            pass
    """
    # Convert UUID to int for advisory lock
    lock_id = int(wallet_id.hex[:16], 16)  # Use first 16 hex chars as int
    
    with connection.cursor() as cursor:
        # Acquire lock
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])
        try:
            yield
        finally:
            # Lock is automatically released when transaction ends
            pass

