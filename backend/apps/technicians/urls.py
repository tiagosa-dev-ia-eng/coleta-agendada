from django.urls import path

from apps.technicians import views

urlpatterns = [
    path(
        "technicians",
        views.TechnicianViewSet.as_view({"get": "list", "post": "create"}),
        name="technician-list",
    ),
    path(
        "technicians/<int:pk>",
        views.TechnicianViewSet.as_view({"get": "retrieve", "patch": "partial_update"}),
        name="technician-detail",
    ),
]
