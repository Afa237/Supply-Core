from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.warehouse_list,
        name="warehouse_list",
    ),
    path(
        "add/",
        views.warehouse_create,
        name="warehouse_create",
    ),
    path(
        "<int:warehouse_id>/edit/",
        views.warehouse_update,
        name="warehouse_update",
    ),
    path(
        "<int:warehouse_id>/delete/",
        views.warehouse_delete,
        name="warehouse_delete",
    ),
]