"""
GraphQL view: схема и debug через app = GraphQL(schema, debug=True).
"""
import json

from ariadne.asgi import GraphQL
from ariadne import graphql_sync
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from main.api.schema import schema

# Схема с включённым debug (стектрейсы и контекст в errors).
# Для полного debug через ASGI: в asgi.py смонтировать app по пути /graphql.
app = GraphQL(schema, debug=True)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def graphql_view(request):
    """Django view для GraphQL (WSGI). Использует schema; debug из settings.DEBUG."""
    if request.method == "GET":
        return JsonResponse({"message": "GraphQL endpoint. Use POST for queries."})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": {"message": "Invalid JSON"}}, status=400)

    success, result = graphql_sync(
        schema,
        data,
        context_value={"request": request},
    )
    status_code = 200 if success else 400
    return JsonResponse(result, status=status_code)
