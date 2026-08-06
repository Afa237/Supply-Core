from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "email",
        "phone",
        "country",
    )

    search_fields = (
        "name",
        "email",
    )

# Register your models here.
