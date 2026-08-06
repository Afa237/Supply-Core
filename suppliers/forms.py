from django import forms

from .models import Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            "name",
            "contact_person",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "website",
            "status",
            "rating",
            "notes",
        ]

        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_rating(self):
        rating = self.cleaned_data["rating"]

        if rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")

        return rating