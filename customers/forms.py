from django import forms

from .models import Customer
from .models import CustomerTransaction

class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer

        fields = [
            "name",
            "customer_type",
            "contact_person",
            "phone",
            "email",
            "address",
            "city",
            "country",
            "status",
            "notes",
        ]

        widgets = {
            "address": forms.Textarea(
                attrs={"rows": 3}
            ),

            "notes": forms.Textarea(
                attrs={"rows": 3}
            ),
        }

class CustomerTransactionForm(forms.ModelForm):

    class Meta:
        model = CustomerTransaction

        fields = [
            "inventory",
            "quantity",
            "reference",
            "notes",
        ]

        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }