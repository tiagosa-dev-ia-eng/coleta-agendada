from django.urls import path

from apps.requests import views, views_results

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
        "requests/<int:pk>/attachments",
        views.RequestViewSet.as_view({"post": "upload_medical_attachments"}),
        name="request-attachments",
    ),
    path(
        "requests/<int:pk>/results",
        views_results.RequestResultsView.as_view(),
        name="request-results",
    ),
    path(
        "results/<int:pk>/publish",
        views_results.ResultPublishView.as_view(),
        name="result-publish",
    ),
    path(
        "results/<token>",
        views_results.PublicResultView.as_view(),
        name="result-public",
    ),
    path(
        "results/<token>/page",
        views_results.PublicResultPageView.as_view(),
        name="result-public-page",
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
