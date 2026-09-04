from django.urls import path

from apps.collection_points import views

urlpatterns = [
    path(
        "collection-points",
        views.CollectionPointViewSet.as_view({"get": "list", "post": "create"}),
        name="collection-point-list",
    ),
    path(
        "collection-points/<int:pk>",
        views.CollectionPointViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update"}
        ),
        name="collection-point-detail",
    ),
    path(
        "collection-points/<int:pk>/windows",
        views.CollectionPointViewSet.as_view({"post": "add_window"}),
        name="collection-point-add-window",
    ),
    path(
        "collection-points/<int:pk>/windows/<int:window_pk>",
        views.CollectionPointViewSet.as_view({"delete": "remove_window"}),
        name="collection-point-remove-window",
    ),
    path(
        "collection-points/<int:pk>/technicians",
        views.CollectionPointViewSet.as_view({"post": "assign_technician"}),
        name="collection-point-assign-technician",
    ),
    path(
        "collection-points/<int:pk>/technicians/<int:technician_pk>",
        views.CollectionPointViewSet.as_view({"delete": "unassign_technician"}),
        name="collection-point-unassign-technician",
    ),
    path(
        "collection-points/<int:pk>/open",
        views.CollectionPointViewSet.as_view({"post": "open"}),
        name="collection-point-open",
    ),
    path(
        "collection-points/<int:pk>/close",
        views.CollectionPointViewSet.as_view({"post": "close"}),
        name="collection-point-close",
    ),
]
