"""
PII (Personally Identifiable Information) masking utilities.
"""
import re
from typing import Any


def mask_email(email: str) -> str:
    """Mask email address."""
    if "@" not in email:
        return email
    parts = email.split("@")
    if len(parts[0]) <= 2:
        masked = "**"
    else:
        masked = parts[0][:2] + "*" * (len(parts[0]) - 2)
    return f"{masked}@{parts[1]}"


def mask_phone(phone: str) -> str:
    """Mask phone number."""
    if len(phone) <= 4:
        return "*" * len(phone)
    return phone[:2] + "*" * (len(phone) - 4) + phone[-2:]


def mask_name(name: str) -> str:
    """Mask name."""
    if len(name) <= 2:
        return "**"
    return name[0] + "*" * (len(name) - 2) + name[-1] if len(name) > 2 else "**"


def mask_uuid(uuid_str: str) -> str:
    """Mask UUID (show first 8 chars only)."""
    if len(uuid_str) < 8:
        return "*" * len(uuid_str)
    return uuid_str[:8] + "-****-****-****-************"


def mask_pii_in_dict(data: dict) -> dict:
    """Mask PII in dictionary recursively."""
    masked = {}
    pii_fields = {
        "email", "phone", "name", "customer_name", "user_id", "customer_id",
        "id", "order_id", "wallet_id", "aggregate_id",
    }
    
    for key, value in data.items():
        key_lower = key.lower()
        
        if isinstance(value, dict):
            masked[key] = mask_pii_in_dict(value)
        elif isinstance(value, list):
            masked[key] = [mask_pii_in_dict(item) if isinstance(item, dict) else item for item in value]
        elif key_lower in pii_fields or "id" in key_lower:
            if isinstance(value, str):
                # Try to detect type and mask accordingly
                if "@" in value:
                    masked[key] = mask_email(value)
                elif re.match(r'^[\d\s\+\-\(\)]+$', value):
                    masked[key] = mask_phone(value)
                elif re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', value, re.I):
                    masked[key] = mask_uuid(value)
                elif "name" in key_lower:
                    masked[key] = mask_name(value)
                else:
                    masked[key] = mask_uuid(value) if len(value) > 10 else value
            else:
                masked[key] = value
        else:
            masked[key] = value
    
    return masked

