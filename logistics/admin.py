from django.contrib import admin

from .models import Driver, Shipment, Vehicle


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "licence_number",
        "active",
    )

    search_fields = (
        "name",
        "phone",
        "licence_number",
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "vehicle_type",
        "capacity",
        "active",
    )

    list_filter = (
        "vehicle_type",
        "active",
    )


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_number",
        "purchase_order",
        "destination_warehouse",
        "status",
        "estimated_delivery_date",
    )

    list_filter = (
        "status",
        "destination_warehouse",
    )

    search_fields = (
        "tracking_number",
        "purchase_order__po_number",
        "origin",
    )

# Register your models here.
