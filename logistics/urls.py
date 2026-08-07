from django.urls import path

from . import views


urlpatterns = [
    path("", views.shipment_list, name="shipment_list"),
    path("add/", views.shipment_create, name="shipment_create"),

    path(
        "<int:shipment_id>/",
        views.shipment_detail,
        name="shipment_detail",
    ),

    path(
        "<int:shipment_id>/edit/",
        views.shipment_update,
        name="shipment_update",
    ),

    path(
        "<int:shipment_id>/delete/",
        views.shipment_delete,
        name="shipment_delete",
    ),

    path("drivers/", views.driver_list, name="driver_list"),
    path(
        "drivers/add/",
        views.driver_create,
        name="driver_create",
    ),

    path("vehicles/", views.vehicle_list, name="vehicle_list"),
    path(
        "vehicles/add/",
        views.vehicle_create,
        name="vehicle_create",
    ),
    path(
        "<int:shipment_id>/receive/",
        views.receive_shipment,
        name="receive_shipment",
    ),
]