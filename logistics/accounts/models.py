from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("admin", "System Administrator"),
        ("supply_chain_manager", "Supply Chain Manager"),
        ("manager", "Department Manager"),
        ("officer", "Officer"),
        ("viewer", "Viewer"),
    ]

    DEPARTMENT_CHOICES = [
        ("administration", "Administration"),
        ("procurement", "Procurement"),
        ("inventory", "Inventory"),
        ("warehouse", "Warehouse"),
        ("logistics", "Logistics"),
        ("finance", "Finance"),
        ("supply_chain", "Supply Chain"),
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

    department = models.CharField(
        max_length=30,
        choices=DEPARTMENT_CHOICES,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.get_department_display() or 'No Department'} - "
            f"{self.get_role_display()}"
        )

    invitation_sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    password_setup_completed = models.BooleanField(
        default=False,
    )

    # Create your models here.
