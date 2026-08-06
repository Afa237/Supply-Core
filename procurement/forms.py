from django import forms

from .models import PurchaseOrder


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            "po_number",
            "supplier",
            "order_date",
            "expected_delivery",
            "status",
            "total_amount",
            "remarks",
        ]

        widgets = {
            "order_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "expected_delivery": forms.DateInput(
                attrs={"type": "date"}
            ),
            "remarks": forms.Textarea(
                attrs={"rows": 3}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        order_date = cleaned_data.get("order_date")
        expected_delivery = cleaned_data.get("expected_delivery")

        if (
            order_date
            and expected_delivery
            and expected_delivery < order_date
        ):
            self.add_error(
                "expected_delivery",
                "Expected delivery cannot be earlier than the order date.",
            )

        return cleaned_data