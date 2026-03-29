import json

from ariadne.asgi import GraphQL
from ariadne import graphql_sync
from ariadne.explorer import ExplorerGraphiQL
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from main.api.graphql.schema import schema

# Схема с включённым debug (стектрейсы и контекст в errors).
# GraphiQL + plugin-explorer: клики по полям в левой панели собирают запрос.
# Для полного debug через ASGI: в asgi.py смонтировать app по пути /graphql.
app = GraphQL(
    schema,
    debug=settings.DEBUG,
    explorer=ExplorerGraphiQL(title="orders_wallet GraphQL", explorer_plugin=True),
)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def graphql_view(request):
    """Django view для GraphQL (WSGI). Использует schema; отладка из settings.DEBUG."""
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
