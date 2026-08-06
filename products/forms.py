from django import forms

from .models import Category, Product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "category",
            "supplier",
            "unit",
            "unit_price",
            "reorder_level",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }