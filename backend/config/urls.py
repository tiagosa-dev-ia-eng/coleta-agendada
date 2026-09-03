"""Rotas raiz do projeto."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # health checks (doc 13 §8) — app core
    path("", include("apps.core.urls")),
    # API v1 (doc 07): módulos entram nos próximos marcos (M1+)
    # path("api/v1/", include("config.api_urls")),
]
