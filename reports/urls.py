from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.reports_dashboard,
        name="reports_dashboard",
    ),
    path(
        "export/csv/",
        views.export_csv,
        name="reports_export_csv",
    ),
    path(
        "export/pdf/",
        views.export_pdf,
        name="reports_export_pdf"
    ),
]