from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "customer_type",
        "phone",
        "city",
        "status",
        "created_at",
    )

    list_filter = (
        "customer_type",
        "status",
        "city",
    )

    search_fields = (
        "name",
        "contact_person",
        "phone",
        "email",
    )

# Register your models here.
