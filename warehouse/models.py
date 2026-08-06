from django.db import models


class Warehouse(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("maintenance", "Under Maintenance"),
    ]

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)

    manager_name = models.CharField(
        max_length=150,
        blank=True,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(blank=True)

    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(
        max_length=100,
        default="Cameroon",
    )

    capacity = models.PositiveIntegerField(
        default=0,
        help_text="Maximum storage capacity",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"
# Create your models here.
