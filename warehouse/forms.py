from django import forms

from .models import Warehouse


class WarehouseForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user and not user.is_superuser:
            profile = user.profile

            if profile.company:
                self.fields["branch"].queryset = (
                    self.fields["branch"].queryset.filter(
                        company=profile.company,
                        active=True,
                    )
                )

            if profile.role not in [
                "admin",
                "supply_chain_manager",
            ]:
                self.fields["branch"].widget = forms.HiddenInput()

    class Meta:
        model = Warehouse
        fields = [
            "branch",
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