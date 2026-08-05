from django.contrib import admin
from .models import UserProfile
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "department",
        "phone_number",
    )

    list_filter = ("role", "department")

    search_fields = (
        "user__username",
        "user__email",
        "department",
    )

# Register your models here.
