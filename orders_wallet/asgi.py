"""
ASGI config for orders_wallet project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders_wallet.settings')

django_application = get_asgi_application()


async def application(scope, receive, send):
    """Роутинг: /graphql — app (GraphQL с debug=True), остальное — Django."""
    path = scope.get("path", "") or ""
    if path == "/graphql" or path == "/graphql/":
        from main.api.views import app
        await app(scope, receive, send)
    else:
        await django_application(scope, receive, send)
