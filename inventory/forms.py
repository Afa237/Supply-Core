from django import forms

from .models import Inventory, StockMovement


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = [
            "product",
            "warehouse",
            "quantity",
        ]


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = [
            "movement_type",
            "quantity",
            "reference",
            "notes",
        ]

        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }