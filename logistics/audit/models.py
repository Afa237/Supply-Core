from django.conf import settings
from django.db import models


class AuditLog(models.Model):

    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("login", "Login"),
        ("logout", "Logout"),
        ("approve", "Approve"),
        ("receive", "Receive"),
        ("status_change", "Status Change"),
        ("permission_change", "Permission Change"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    department = models.CharField(
        max_length=50,
        blank=True,
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
    )

    model_name = models.CharField(
        max_length=100,
    )

    object_id = models.CharField(
        max_length=100,
        blank=True,
    )

    object_repr = models.CharField(
        max_length=255,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        username = (
            self.user.username
            if self.user
            else "System"
        )

        return (
            f"{username} - "
            f"{self.action} - "
            f"{self.model_name}"
        )

# Create your models here.
