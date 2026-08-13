from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import (
    department_required,
    role_required,
)
from .forms import WarehouseForm
from .models import Warehouse


@login_required
@department_required("warehouse")
@role_required("viewer")
def warehouse_list(request):
    warehouses = Warehouse.objects.all()

    query = request.GET.get("q", "")
    status = request.GET.get("status", "")

    if query:
        warehouses = warehouses.filter(
            Q(name__icontains=query)
            | Q(code__icontains=query)
            | Q(city__icontains=query)
            | Q(manager_name__icontains=query)
        )

    if status:
        warehouses = warehouses.filter(status=status)

    return render(
        request,
        "warehouse/warehouse_list.html",
        {
            "warehouses": warehouses,
            "query": query,
            "selected_status": status,
        },
    )


@login_required
@department_required("warehouse")
@role_required("officer")
def warehouse_create(request):
    if request.method == "POST":
        form = WarehouseForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("warehouse_list")
    else:
        form = WarehouseForm()

    return render(
        request,
        "warehouse/warehouse_form.html",
        {
            "form": form,
            "page_title": "Add Warehouse",
        },
    )


@login_required
@department_required("warehouse")
@role_required("officer")
def warehouse_update(request, warehouse_id):
    warehouse = get_object_or_404(
        Warehouse,
        id=warehouse_id,
    )

    if request.method == "POST":
        form = WarehouseForm(
            request.POST,
            instance=warehouse,
        )

        if form.is_valid():
            form.save()
            return redirect("warehouse_list")
    else:
        form = WarehouseForm(instance=warehouse)

    return render(
        request,
        "warehouse/warehouse_form.html",
        {
            "form": form,
            "page_title": "Edit Warehouse",
        },
    )


@login_required
@department_required("warehouse")
@role_required("manager")
def warehouse_delete(request, warehouse_id):
    warehouse = get_object_or_404(
        Warehouse,
        id=warehouse_id,
    )

    if request.method == "POST":
        warehouse.delete()
        return redirect("warehouse_list")

    return render(
        request,
        "warehouse/warehouse_confirm_delete.html",
        {"warehouse": warehouse},
    )

# Create your views here.
