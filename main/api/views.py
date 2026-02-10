"""
GraphQL view with idempotency and logging support.
"""
import hashlib
import json
import logging
import time
from uuid import UUID, uuid4

from ariadne import graphql_sync
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from main.api.schema import schema
from main.infra.models.service_models.models import IdempotencyKey

logger = logging.getLogger(__name__)


class OrdersWalletGraphQLView:
    """GraphQL view with idempotency and structured logging."""

    def dispatch(self, request, *args, **kwargs):
        """Handle GraphQL request with idempotency."""
        # Extract request ID and idempotency key
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        idempotency_key = request.headers.get("Idempotency-Key")
        user_id = request.headers.get("X-User-ID")

        # Log request (with PII masking)
        log_data = {
            "request_id": request_id,
            "user_id": mask_uuid(user_id) if user_id else None,
            "idempotency_key": idempotency_key[:8] + "..." if idempotency_key else None,
            "operation": "graphql",
        }
        logger.info("graphql_request", extra=mask_pii_in_dict(log_data))

        # Handle idempotency for mutations
        if idempotency_key and request.method == "POST":
            try:
                body = request.body.decode("utf-8")
                data = json.loads(body)
                operation_name = data.get("operationName", "")
                variables = data.get("variables", {})

                # Check if this is a mutation
                query = data.get("query", "")
                is_mutation = "mutation" in query.lower()

                if is_mutation and user_id:
                    # Create request hash
                    request_hash = self._create_request_hash(query, variables)

                    # Validate and convert user_id to UUID
                    try:
                        user_uuid = UUID(user_id)
                    except (ValueError, TypeError):
                        logger.warning(
                            "invalid_user_id",
                            extra={
                                "request_id": request_id,
                                "user_id": user_id,
                            }
                        )
                        user_uuid = None

                    # Check for existing idempotency key
                    existing = None
                    if user_uuid:
                        existing = IdempotencyKey.objects.filter(
                            key=idempotency_key,
                            user_id=user_uuid,
                            operation=self._extract_operation(operation_name),
                        ).first()

                    if existing:
                        # Check if request hash matches (same request)
                        if existing.request_hash == request_hash:
                            # Return cached response
                            logger.info(
                                "idempotent_request_cached",
                                extra={
                                    "request_id": request_id,
                                    "user_id": user_id,
                                    "idempotency_key": idempotency_key,
                                    "operation": self._extract_operation(operation_name),
                                }
                            )
                            return JsonResponse(
                                existing.response_payload,
                                safe=False,
                            )
                        else:
                            # Different request with same key - conflict
                            logger.warning(
                                "idempotency_key_conflict",
                                extra={
                                    "request_id": request_id,
                                    "user_id": user_id,
                                    "idempotency_key": idempotency_key,
                                }
                            )
                            return JsonResponse(
                                {
                                    "error": {
                                        "code": "DUPLICATE_REQUEST",
                                        "message": "Idempotency key already used with different request",
                                    }
                                },
                                status=409,
                            )

                    # Process request
                    response = self._process_graphql_request(request)

                    # Save idempotency key (if response is successful)
                    if response.status_code == 200 and user_uuid:
                        try:
                            response_data = json.loads(response.content)
                            IdempotencyKey.objects.create(
                                key=idempotency_key,
                                user_id=user_uuid,
                                operation=self._extract_operation(operation_name),
                                request_hash=request_hash,
                                response_payload=response_data,
                            )
                        except Exception as e:
                            logger.error(
                                "failed_to_save_idempotency",
                                extra={
                                    "request_id": request_id,
                                    "error": str(e),
                                }
                            )

                    return response
            except Exception as e:
                logger.error(
                    "idempotency_error",
                    extra={
                        "request_id": request_id,
                        "error": str(e),
                    }
                )

        # Process request normally
        try:
            response = self._process_graphql_request(request)
        except Exception as e:
            # Handle errors
            response = ErrorHandler.handle_error(e)
            logger.error(
                "graphql_error",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "error": str(e),
                }
            )

        # Log response
        logger.info(
            "graphql_response",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "status": response.status_code,
            }
        )

        return response

    def _create_request_hash(self, query: str, variables: dict) -> str:
        """Create hash of request for deduplication."""
        content = json.dumps({"query": query, "variables": variables}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def _extract_operation(self, operation_name: str) -> str:
        """Extract operation type from operation name."""
        if "createOrder" in operation_name:
            return "CREATE_ORDER"
        elif "capturePayment" in operation_name:
            return "CAPTURE_PAYMENT"
        elif "refundOrder" in operation_name:
            return "REFUND_ORDER"
        return "UNKNOWN"

    def _process_graphql_request(self, request):
        """Process GraphQL request."""
        if request.method == "GET":
            # For GET requests, return schema info or empty response
            return JsonResponse({"message": "GraphQL endpoint. Use POST for queries."})

        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": {"message": "Invalid JSON"}},
                status=400
            )

        # Execute GraphQL query
        success, result = graphql_sync(
            schema,
            data,
            context_value={"request": request}
        )

        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H2", "location": "views.py:207", "message": "graphql_execution_result", "data": {"success": success, "has_errors": "errors" in result if result else False}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion

        status_code = 200 if success else 400
        return JsonResponse(result, status=status_code)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def graphql_view(request):
    """GraphQL endpoint."""
    view = OrdersWalletGraphQLView()
    return view.dispatch(request)

