from __future__ import annotations

from graphql import GraphQLError

from main.domain.errors import DomainError


def domain_error_payload(*, status: str, error: DomainError, **extra_fields) -> dict:
    payload = dict(extra_fields)
    payload["status"] = status
    payload["errorCode"] = error.code
    payload["errorMessage"] = error.message
    return payload


def internal_error(exc: Exception) -> GraphQLError:
    return GraphQLError(
        "Internal server error",
        extensions={"code": "INTERNAL_ERROR", "details": exc.__class__.__name__},
    )


def run_with_hybrid_errors(handler, *, on_domain_error=None):
    try:
        return handler()
    except DomainError as exc:
        if on_domain_error is not None:
            return on_domain_error(exc)
        raise GraphQLError(exc.message, extensions={"code": exc.code}) from exc
    except Exception as exc:
        raise internal_error(exc) from exc
