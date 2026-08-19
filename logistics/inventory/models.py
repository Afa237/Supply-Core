from django.conf import settings
from django.db import models

from products.models import Product
from warehouse.models import Warehouse


class Inventory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory_records",
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="inventory_records",
    )

    quantity = models.PositiveIntegerField(default=0)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("product", "warehouse")
        ordering = ["product__name", "warehouse__name"]

    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name}"

    @property
    def is_low_stock(self):
        return self.quantity <= self.product.reorder_level


class StockMovement(models.Model):
    MOVEMENT_CHOICES = [
        ("stock_in", "Stock In"),
        ("stock_out", "Stock Out"),
        ("adjustment", "Adjustment"),
    ]

    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name="movements",
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_CHOICES,
    )

    quantity = models.PositiveIntegerField()

    reference = models.CharField(
        max_length=100,
        blank=True,
    )

    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.get_movement_type_display()} - "
            f"{self.inventory.product.name}"
        )
# Create your models here.
