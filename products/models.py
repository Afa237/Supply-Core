from django.db import models
from suppliers.models import Supplier


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):

    UNIT_CHOICES = [
        ("pcs", "Pieces"),
        ("kg", "Kilograms"),
        ("ltr", "Litres"),
        ("box", "Boxes"),
        ("carton", "Cartons"),
        ("bag", "Bags")
    ]

    name = models.CharField(max_length=200)

    sku = models.CharField(
        max_length=50,
        unique=True
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default="pcs"
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reorder_level = models.PositiveIntegerField(default=10)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Create your models here.
