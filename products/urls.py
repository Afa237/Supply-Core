from django.urls import path

from . import views


urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("add/", views.product_create, name="product_create"),
    path("<int:product_id>/edit/", views.product_update, name="product_update"),
    path("<int:product_id>/delete/", views.product_delete, name="product_delete"),

    path("categories/", views.category_list, name="category_list"),
    path("categories/add/", views.category_create, name="category_create"),
]