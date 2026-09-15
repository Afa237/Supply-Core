from django.contrib import admin
from .models import Company, Branch, UserProfile


class BranchInline(admin.TabularInline):
    model = Branch
    extra = 1


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "country", "active")
    search_fields = ("name", "code")
    list_filter = ("country", "active")
    inlines = [BranchInline]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "company",
        "code",
        "city",
        "country",
        "active",
    )
    list_filter = (
        "company",
        "country",
        "active",
    )
    search_fields = (
        "name",
        "code",
        "city",
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company",
        "branch",
        "department",
        "role",
    )
    list_filter = (
        "company",
        "branch",
        "department",
        "role",
    )
