from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SupplierForm
from .models import Supplier


@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()

    query = request.GET.get("q")

    if query:
        suppliers = suppliers.filter(name__icontains=query)

    return render(
        request,
        "suppliers/supplier_list.html",
        {
            "suppliers": suppliers,
            "query": query or "",
        },
    )


@login_required
def supplier_create(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("supplier_list")
    else:
        form = SupplierForm()

    return render(
        request,
        "suppliers/supplier_form.html",
        {
            "form": form,
            "page_title": "Add Supplier",
        },
    )


@login_required
def supplier_update(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)

    if request.method == "POST":
        form = SupplierForm(request.POST, instance=supplier)

        if form.is_valid():
            form.save()
            return redirect("supplier_list")
    else:
        form = SupplierForm(instance=supplier)

    return render(
        request,
        "suppliers/supplier_form.html",
        {
            "form": form,
            "page_title": "Edit Supplier",
        },
    )


@login_required
def supplier_delete(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)

    if request.method == "POST":
        supplier.delete()
        return redirect("supplier_list")

    return render(
        request,
        "suppliers/supplier_confirm_delete.html",
        {"supplier": supplier},
    )