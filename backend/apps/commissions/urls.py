from django.urls import path

from apps.commissions import views

urlpatterns = [
    path(
        "commission-rules",
        views.CommissionRuleListCreateView.as_view(),
        name="commission-rule-list",
    ),
    path(
        "commission-rules/<int:pk>",
        views.CommissionRuleUpdateView.as_view(),
        name="commission-rule-detail",
    ),
    path("commissions", views.CommissionListView.as_view(), name="commission-list"),
    path(
        "commissions/<int:pk>",
        views.CommissionDetailView.as_view(),
        name="commission-detail",
    ),
    path(
        "commissions/<int:pk>/mark-paid",
        views.CommissionMarkPaidView.as_view(),
        name="commission-mark-paid",
    ),
    path(
        "commissions/<int:pk>/reverse",
        views.CommissionReverseView.as_view(),
        name="commission-reverse",
    ),
]
