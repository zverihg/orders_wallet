"""
Pytest configuration for Django tests.
"""

import os
import django

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orders_wallet.settings")

# Configure Django
django.setup()
