from django.urls import path

from apps.audit import views

urlpatterns = [
    path("audit", views.AuditLogListView.as_view(), name="audit-log-list"),
]
