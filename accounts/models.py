from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("admin", "System Administrator"),
        ("supply_chain_manager", "Supply Chain Manager"),
        ("procurement_officer", "Procurement Officer"),
        ("warehouse_manager", "Warehouse Manager"),
        ("inventory_officer", "Inventory Officer"),
        ("logistics_officer", "Logistics Officer"),
        ("finance_officer", "Finance Officer"),
        ("viewer", "Viewer"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default="viewer",
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    department = models.CharField(
        max_length=100,
        blank=True,
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

# Create your models here.
