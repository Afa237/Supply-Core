from django.db import models
from suppliers.models import Supplier
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

# Create your models here.
