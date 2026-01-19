"""
Custom JSON formatter for logging (without external dependencies).
"""
import json
import logging
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "operation"):
            log_data["operation"] = record.operation
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "idempotency_key"):
            log_data["idempotency_key"] = record.idempotency_key
        if hasattr(record, "error"):
            log_data["error"] = record.error

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)

