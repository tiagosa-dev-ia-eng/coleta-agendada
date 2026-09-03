from django.urls import path

from apps.scheduling import views

urlpatterns = [
    path(
        "requests/<int:pk>/appointment",
        views.ScheduleAppointmentView.as_view(),
        name="request-appointment",
    ),
    path("appointments", views.AppointmentListView.as_view(), name="appointment-list"),
    path(
        "appointments/<int:pk>",
        views.AppointmentDetailView.as_view(),
        name="appointment-detail",
    ),
    path(
        "appointments/<int:pk>/check-in",
        views.AppointmentCheckinView.as_view(),
        name="appointment-checkin",
    ),
    path(
        "appointments/<int:pk>/check-out",
        views.AppointmentCheckoutView.as_view(),
        name="appointment-checkout",
    ),
    path(
        "appointments/<int:pk>/complete",
        views.AppointmentCompleteView.as_view(),
        name="appointment-complete",
    ),
]
