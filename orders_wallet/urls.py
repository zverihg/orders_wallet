"""
URL configuration for orders_wallet project.
"""
from django.contrib import admin
from django.urls import path

from main.api.views import graphql_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', graphql_view, name='graphql'),
]
