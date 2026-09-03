from django.urls import path

from apps.quotations import views

urlpatterns = [
    path(
        "requests/<int:pk>/quotation-draft",
        views.QuotationDraftView.as_view(),
        name="quotation-draft",
    ),
    path(
        "requests/<int:pk>/quotations",
        views.RequestQuotationsView.as_view(),
        name="request-quotations",
    ),
    path("quotations/<int:pk>", views.QuotationDetailView.as_view(), name="quotation-detail"),
    path(
        "quotations/<int:pk>/validate",
        views.QuotationValidateView.as_view(),
        name="quotation-validate",
    ),
    path("quotations/<int:pk>/send", views.QuotationSendView.as_view(), name="quotation-send"),
    path(
        "quotations/<int:pk>/approve",
        views.QuotationApproveView.as_view(),
        name="quotation-approve",
    ),
    path(
        "quotations/<int:pk>/reject",
        views.QuotationRejectView.as_view(),
        name="quotation-reject",
    ),
]
