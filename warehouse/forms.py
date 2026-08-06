from django import forms

from .models import Warehouse


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = [
            "name",
            "code",
            "manager_name",
            "phone",
            "email",
            "address",
            "city",
            "country",
            "capacity",
            "status",
            "notes",
        ]

        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }