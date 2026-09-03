from django.urls import path

from apps.requests import views

urlpatterns = [
    path(
        "requests",
        views.RequestViewSet.as_view({"get": "list", "post": "create"}),
        name="request-list",
    ),
    path(
        "requests/<int:pk>",
        views.RequestViewSet.as_view({"get": "retrieve"}),
        name="request-detail",
    ),
    path(
        "requests/<int:pk>/cancel",
        views.RequestViewSet.as_view({"post": "cancel"}),
        name="request-cancel",
    ),
    path(
        "requests/<int:pk>/history",
        views.RequestViewSet.as_view({"get": "history"}),
        name="request-history",
    ),
    path(
        "requests/<int:pk>/medical-orders",
        views.RequestViewSet.as_view(
            {"get": "list_medical_orders", "post": "upload_medical_order"}
        ),
        name="medical-order-list",
    ),
]
