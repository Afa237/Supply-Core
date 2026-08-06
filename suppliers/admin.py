from django.contrib import admin

from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "contact_person",
        "phone",
        "country",
        "status",
        "rating",
    )

    list_filter = ("status", "country", "rating")

    search_fields = (
        "name",
        "contact_person",
        "email",
        "phone",
    )

# Register your models here.
