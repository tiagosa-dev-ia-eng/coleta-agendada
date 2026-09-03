"""Rotas da API v1 (doc 07). Módulos novos entram aqui por marco."""
from django.urls import include, path

urlpatterns = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.organizations.urls")),
    path("", include("apps.technicians.urls")),
    path("", include("apps.patients.urls")),
]
