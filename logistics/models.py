from django.conf import settings
from django.db import models

from procurement.models import PurchaseOrder
from warehouse.models import Warehouse


class Driver(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    licence_number = models.CharField(max_length=50, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ("truck", "Truck"),
        ("van", "Van"),
        ("pickup", "Pickup"),
        ("motorcycle", "Motorcycle"),
        ("other", "Other"),
    ]

    registration_number = models.CharField(
        max_length=50,
        unique=True,
    )

    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPES,
        default="truck",
    )

    capacity = models.PositiveIntegerField(
        default=0,
        help_text="Vehicle carrying capacity",
    )

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.registration_number


class Shipment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("packed", "Packed"),
        ("dispatched", "Dispatched"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("delayed", "Delayed"),
        ("cancelled", "Cancelled"),
    ]

    tracking_number = models.CharField(
        max_length=50,
        unique=True,
    )

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name="shipments",
    )

    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="incoming_shipments",
    )

    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    
    inventory_received = models.BooleanField(default=False)

    dispatch_date = models.DateField(
        null=True,
        blank=True,
    )

    estimated_delivery_date = models.DateField()

    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
    )

    origin = models.CharField(max_length=200)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.tracking_number

# Create your models here.
