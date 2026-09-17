from django import forms
from accounts.access import filter_by_user_scope 
from accounts.models import Branch 
from inventory.models import Inventory
from .models import ( Customer, CustomerTransaction, )


class CustomerForm(forms.ModelForm):
    def __init__(
        self,
        *args,
        user=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        if not user:
            self.fields["branch"].queryset = (
                Branch.objects.none()
            )
            return

        # Superuser may access all active branches.
        if user.is_superuser:

            self.fields["branch"].queryset = (
                Branch.objects.filter(
                    active=True
                ).order_by(
                    "company__name",
                    "name",
                )
            )

            return

        profile = getattr(
            user,
            "profile",
            None,
        )

        if not profile:
            self.fields["branch"].queryset = (
                Branch.objects.none()
            )
            return

        # Only branches belonging to the user's company.
        if profile.company:

            self.fields["branch"].queryset = (
                Branch.objects.filter(
                    company=profile.company,
                    active=True,
                ).order_by("name")
            )

        else:

            self.fields["branch"].queryset = (
                Branch.objects.none()
            )

        # Branch-level employees do not choose another branch.
        if profile.role not in [
            "admin",
            "supply_chain_manager",
        ]:

            self.fields["branch"].widget = (
                forms.HiddenInput()
            )

    class Meta:

        model = Customer

        fields = [
            "branch",
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
                attrs={
                    "rows": 3,
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }


class CustomerTransactionForm(forms.ModelForm):
    def __init__(
        self,
        *args,
        user=None,
        customer=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        inventory_records = (
            Inventory.objects.select_related(
                "product",
                "warehouse",
                "warehouse__branch",
            )
        )

        if user:

            inventory_records = (
                filter_by_user_scope(
                    inventory_records,
                    user,
                    branch_field=(
                        "warehouse__branch"
                    ),
                )
            )

        else:

            inventory_records = (
                Inventory.objects.none()
            )

        # A dispatch for a customer must use stock
        # from the customer's own branch.
        if customer and customer.branch:

            inventory_records = (
                inventory_records.filter(
                    warehouse__branch=(
                        customer.branch
                    )
                )
            )

        self.fields[
            "inventory"
        ].queryset = (
            inventory_records.order_by(
                "product__name",
                "warehouse__name",
            )
        )

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