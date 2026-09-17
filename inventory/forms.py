from django import forms
from .models import Inventory, StockMovement 
from warehouse.models import Warehouse 
from accounts.access import filter_by_user_scope

class InventoryForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            self.fields["warehouse"].queryset = filter_by_user_scope(
                Warehouse.objects.all(),
                user,
            )

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
            "notes": forms.Textarea(
                attrs={"rows": 3}
            ),
        }