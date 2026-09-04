from django.urls import path

from apps.catalog import views

urlpatterns = [
    path(
        "exams",
        views.ExamViewSet.as_view({"get": "list", "post": "create"}),
        name="exam-list",
    ),

    path(
        "exams/<int:pk>",
        views.ExamViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="exam-detail",
    ),
    path(
        "exams/<int:pk>/price",
        views.ExamViewSet.as_view({"post": "set_price"}),
        name="exam-price",
    ),
]
