from django.contrib import admin

from .models import Inventory, StockMovement


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "warehouse",
        "quantity",
        "last_updated",
    )

    list_filter = ("warehouse",)

    search_fields = (
        "product__name",
        "product__sku",
        "warehouse__name",
    )


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "inventory",
        "movement_type",
        "quantity",
        "created_by",
        "created_at",
    )

    list_filter = (
        "movement_type",
        "created_at",
    )

# Register your models here.
