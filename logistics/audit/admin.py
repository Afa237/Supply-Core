from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "created_at",
        "user",
        "department",
        "action",
        "model_name",
        "object_repr",
    )

    list_filter = (
        "action",
        "department",
        "model_name",
        "created_at",
    )

    search_fields = (
        "user__username",
        "object_repr",
        "description",
        "model_name",
    )

    readonly_fields = (
        "user",
        "department",
        "action",
        "model_name",
        "object_id",
        "object_repr",
        "description",
        "metadata",
        "ip_address",
        "created_at",
    )

# Register your models here.
