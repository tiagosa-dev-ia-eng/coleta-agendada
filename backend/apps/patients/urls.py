from django.urls import path

from apps.patients import views

urlpatterns = [
    path(
        "patients",
        views.PatientViewSet.as_view({"get": "list", "post": "create"}),
        name="patient-list",
    ),
    path(
        "patients/<int:pk>",
        views.PatientViewSet.as_view({"get": "retrieve"}),
        name="patient-detail",
    ),
]
