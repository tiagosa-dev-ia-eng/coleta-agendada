from django.urls import path

from apps.organizations import views

urlpatterns = [
    path(
        "laboratories",
        views.LaboratoryViewSet.as_view({"get": "list", "post": "create"}),
        name="laboratory-list",
    ),
    path(
        "laboratories/<int:pk>",
        views.LaboratoryViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="laboratory-detail",
    ),
    path(
        "resellers",
        views.ResellerViewSet.as_view({"get": "list", "post": "create"}),
        name="reseller-list",
    ),
    path(
        "pharmacies",
        views.PharmacyViewSet.as_view({"get": "list", "post": "create"}),
        name="pharmacy-list",
    ),
    path(
        "pharmacies/<int:pk>",
        views.PharmacyViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="pharmacy-detail",
    ),
]
