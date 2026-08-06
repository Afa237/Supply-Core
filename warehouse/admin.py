from django.contrib import admin

from .models import Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "manager_name",
        "city",
        "capacity",
        "status",
    )

    list_filter = (
        "status",
        "city",
        "country",
    )

    search_fields = (
        "name",
        "code",
        "manager_name",
        "city",
    )
# Register your models here.
