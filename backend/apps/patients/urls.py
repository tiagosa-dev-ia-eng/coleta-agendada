from django.urls import path

from apps.patients import views, views_privacy

urlpatterns = [
    path(
        "patients",
        views.PatientViewSet.as_view({"get": "list", "post": "create"}),
        name="patient-list",
    ),

    path(
        "patients/me/consent",
        views_privacy.PatientConsentView.as_view(),
        name="patient-me-consent",
    ),
    path(
        "patients/me/export",
        views_privacy.PatientDataExportView.as_view(),
        name="patient-me-export",
    ),
    path(
        "patients/me/anonymize",
        views_privacy.PatientAnonymizeView.as_view(),
        name="patient-me-anonymize",
    ),
    path(
        "patients/<int:pk>",
        views.PatientViewSet.as_view({"get": "retrieve"}),
        name="patient-detail",
    ),
]
