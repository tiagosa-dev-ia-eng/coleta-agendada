"""Rotas da API v1 (doc 07). Módulos novos entram aqui por marco."""
from apps.core import views as core_views
from django.urls import include, path

urlpatterns = [
    path("version", core_views.version, name="api-version"),
    path("", include("apps.accounts.urls")),
    path("", include("apps.organizations.urls")),
    path("", include("apps.collection_points.urls")),
    path("", include("apps.technicians.urls")),
    path("", include("apps.patients.urls")),
    path("", include("apps.requests.urls")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.quotations.urls")),
    path("", include("apps.scheduling.urls")),
    path("", include("apps.payments.urls")),
    path("", include("apps.commissions.urls")),
    path("", include("apps.whatsapp.urls")),
    path("", include("apps.audit.urls")),
]
