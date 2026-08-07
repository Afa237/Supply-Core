from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        "po_number",
        "supplier",
        "status",
        "order_date",
        "expected_delivery",
    )

    inlines = [PurchaseOrderItemInline]


admin.site.register(PurchaseOrderItem)

# Register your models here.
