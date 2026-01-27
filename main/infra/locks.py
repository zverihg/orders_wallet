"""
Distributed locks using PostgreSQL advisory locks.
"""
from contextlib import contextmanager
from uuid import UUID

from django.db import connection


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
    # Use PostgreSQL hashtext to convert UUID string to a consistent bigint
    with connection.cursor() as cursor:
        # Acquire lock using hashtext to ensure we get a valid bigint
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s)::bigint)",
            [str(wallet_id)]
        )
        try:
            yield
        finally:
            # Lock is automatically released when transaction ends
            pass

