from django import forms

from .models import Driver, Shipment, Vehicle


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = [
            "name",
            "phone",
            "licence_number",
            "active",
        ]


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "registration_number",
            "vehicle_type",
            "capacity",
            "active",
        ]


class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = [
            "tracking_number",
            "purchase_order",
            "destination_warehouse",
            "driver",
            "vehicle",
            "status",
            "dispatch_date",
            "estimated_delivery_date",
            "actual_delivery_date",
            "origin",
            "notes",
        ]

        widgets = {
            "dispatch_date": forms.DateInput(attrs={"type": "date"}),
            "estimated_delivery_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "actual_delivery_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()

        dispatch_date = cleaned_data.get("dispatch_date")
        estimated_delivery = cleaned_data.get(
            "estimated_delivery_date"
        )
        actual_delivery = cleaned_data.get(
            "actual_delivery_date"
        )
        status = cleaned_data.get("status")

        if (
            dispatch_date
            and estimated_delivery
            and estimated_delivery < dispatch_date
        ):
            self.add_error(
                "estimated_delivery_date",
                "Estimated delivery cannot be before dispatch.",
            )

        if (
            actual_delivery
            and dispatch_date
            and actual_delivery < dispatch_date
        ):
            self.add_error(
                "actual_delivery_date",
                "Actual delivery cannot be before dispatch.",
            )

        if status == "delivered" and not actual_delivery:
            self.add_error(
                "actual_delivery_date",
                "Enter the actual delivery date.",
            )

        return cleaned_data