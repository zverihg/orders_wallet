"""
Middleware for request validation and error handling.
"""
import logging
from uuid import UUID

from django.http import JsonResponse

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error."""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ErrorHandler:
    """Error handler for API responses."""

    ERROR_CODES = {
        "VALIDATION_ERROR": 400,
        "NOT_FOUND": 404,
        "INSUFFICIENT_BALANCE": 400,
        "INVALID_STATE": 400,
        "DUPLICATE_REQUEST": 409,
        "INTERNAL_ERROR": 500,
    }

    @classmethod
    def handle_error(cls, error: Exception) -> JsonResponse:
        """Handle error and return JSON response."""
        if isinstance(error, ValidationError):
            status_code = cls.ERROR_CODES.get(error.code, 400)
            return JsonResponse(
                {
                    "error": {
                        "code": error.code,
                        "message": error.message,
                    }
                },
                status=status_code,
            )

        # Log unexpected errors
        logger.error(
            "unexpected_error",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
            exc_info=True,
        )

        return JsonResponse(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                }
            },
            status=500,
        )

