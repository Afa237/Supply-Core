from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.alert_list,
        name="alert_list",
    ),

    path(
        "<int:alert_id>/acknowledge/",
        views.acknowledge_alert,
        name="acknowledge_alert",
    ),

    path(
        "<int:alert_id>/resolve/",
        views.resolve_alert_view,
        name="resolve_alert",
    ),

]