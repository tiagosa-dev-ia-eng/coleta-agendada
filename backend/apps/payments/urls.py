from django.urls import path

from apps.payments import views

urlpatterns = [
    path(
        "requests/<int:pk>/payments",
        views.RequestPaymentsView.as_view(),
        name="request-payments",
    ),
    path(
        "requests/<int:pk>/payments/link",
        views.PaymentLinkView.as_view(),
        name="payment-link",
    ),
    path("payments/<int:pk>", views.PaymentDetailView.as_view(), name="payment-detail"),
    path(
        "payments/<int:pk>/confirm",
        views.PaymentConfirmView.as_view(),
        name="payment-confirm",
    ),
    path("payments/webhook", views.PaymentWebhookView.as_view(), name="payment-webhook"),
]
