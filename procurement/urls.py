from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.purchase_order_list,
        name="purchase_order_list",
    ),
    path(
        "add/",
        views.purchase_order_create,
        name="purchase_order_create",
    ),
    path(
        "<int:po_id>/",
        views.purchase_order_detail,
        name="purchase_order_detail",
    ),
    path(
        "<int:po_id>/edit/",
        views.purchase_order_update,
        name="purchase_order_update",
    ),
    path(
        "<int:po_id>/delete/",
        views.purchase_order_delete,
        name="purchase_order_delete",
    ),
    path(
    "<int:po_id>/items/add/",
    views.purchase_order_item_create,
    name="purchase_order_item_create",
    ),
    path(
        "items/<int:item_id>/edit/",
        views.purchase_order_item_update,
        name="purchase_order_item_update",
        ),
    path(
        "items/<int:item_id>/delete/",
        views.purchase_order_item_delete,
        name="purchase_order_item_delete",
        ),
]