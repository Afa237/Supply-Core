from django.db import models
from suppliers.models import Supplier
from products.models import Product

class PurchaseOrder(models.Model):

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("ordered", "Ordered"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    ]

    po_number = models.CharField(
        max_length=30,
        unique=True,
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
    )

    order_date = models.DateField()

    expected_delivery = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.po_number
    @property
    def calculated_total(self):
        return sum(item.total for item in self.items.all())

class PurchaseOrderItem(models.Model):

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        unique_together = ("purchase_order", "product")

    @property
    def total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.product.name}"

# Create your models here.
