from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import (
    department_required,
    role_required,
)
from .forms import WarehouseForm
from .models import Warehouse
import csv
from django.http import HttpResponse
from accounts.access import filter_by_user_scope




@login_required
@department_required("warehouse")
@role_required("viewer")
def warehouse_list(request):
    warehouses = Warehouse.objects.select_related(
        "branch",
        "branch__company",
        ).all()
    warehouses = filter_by_user_scope(
        warehouses,
        request.user,
    )

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
        form = WarehouseForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():
            warehouse = form.save(commit=False)
            profile = request.user.profile

            if profile.role not in [
                "admin",
                "supply_chain_manager",
            ] and not request.user.is_superuser:
                warehouse.branch = profile.branch

            if not warehouse.branch:
                messages.error(
                    request,
                    "Please select a branch.",
                )
            else:
                warehouse.save()
                messages.success(
                    request,
                    "Warehouse created successfully.",
                )
            return redirect("warehouse_list")

    else:
        form = WarehouseForm(
            user=request.user
        )

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
    warehouse = filter_by_user_scope(
    Warehouse.objects.all(),
    request.user,
    )
    warehouse = get_object_or_404(
        Warehouse,
        id=warehouse_id,
    )

    if request.method == "POST":
        form = WarehouseForm(
            request.POST,
            instance=warehouse,
            user=request.user,
        )

        if form.is_valid():
            form.save()
            return redirect("warehouse_list")
    else:
        form = WarehouseForm(instance=warehouse, user=request.user)

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
@role_required("admin")
def warehouse_delete(request, warehouse_id):
    warehouse = filter_by_user_scope(
    Warehouse.objects.all(),
    request.user,
    )
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
@login_required 
@department_required("warehouse") 
@role_required("viewer") 
def warehouse_export_csv(request):
    warehouses = Warehouse.objects.select_related(
        "branch",
        "branch__company",
        ).all()
    warehouses = filter_by_user_scope(
        warehouses,
        request.user,
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="warehouses.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "Name",
        "Code",
        "Manager",
        "City",
        "Country",
        "Capacity",
        "Status",
        "Company",
        "Branch",
    ])

    for warehouse in warehouses:
        writer.writerow([
            warehouse.name,
            warehouse.code,
            warehouse.manager_name,
            warehouse.city,
            warehouse.country,
            warehouse.capacity,
            warehouse.get_status_display(),
            warehouse.branch.company.name if warehouse.branch else "",
            warehouse.branch.name if warehouse.branch else "",
        ])

    return response

# Create your views here.
