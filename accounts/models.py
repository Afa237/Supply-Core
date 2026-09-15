from django.conf import settings
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(
        max_length=30,
        unique=True,
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(
        max_length=30,
        blank=True,
    )
    country = models.CharField(
        max_length=100,
        blank=True,
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Branch(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="branches",
    )
    name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        )
    code = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )
    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    address = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    
    created_at =  models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["company__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"],
                name="unique_branch_code_per_company",
            )
        ]

    def __str__(self):
        return f"{self.company.name} - {self.name}"


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

    invitation_sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    password_setup_completed = models.BooleanField(
        default=False,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.get_department_display() or 'No Department'} - "
            f"{self.get_role_display()}"
        )
