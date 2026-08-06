from django.urls import path
from . import views

urlpatterns = [
    path("", views.inventory_list, name="inventory_list"),
    path("add/", views.inventory_create, name="inventory_create"),
    path(
        "<int:inventory_id>/edit/",
        views.inventory_update,
        name="inventory_update",
    ),
    path(
        "<int:inventory_id>/movement/",
        views.stock_movement_create,
        name="stock_movement_create",
    ),
    path(
        "movements/",
        views.stock_movement_list,
        name="stock_movement_list",
    ),
]