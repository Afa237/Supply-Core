from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from warehouse.models import Warehouse
from accounts.decorators import (
    department_required,
    role_required,
)
from .forms import InventoryForm, StockMovementForm
from .models import Inventory, StockMovement
from notifications.services import create_alert
from django.db import models


@login_required
@department_required("inventory")
@role_required("viewer")
def inventory_list(request):
    inventory_records = Inventory.objects.select_related(
        "product",
        "warehouse",
    )

    warehouses = Warehouse.objects.all()

    query = request.GET.get("q", "")
    warehouse_id = request.GET.get("warehouse", "")
    stock_status = request.GET.get("status", "")

    if query:
        inventory_records = inventory_records.filter(
            Q(product__name__icontains=query)
            | Q(product__sku__icontains=query)
            | Q(warehouse__name__icontains=query)
        )

    if warehouse_id:
        inventory_records = inventory_records.filter(
            warehouse_id=warehouse_id
        )

    if stock_status == "low":
        inventory_records = [
            record
            for record in inventory_records
            if record.is_low_stock
        ]

    low_stock_items = Inventory.objects.filter(
        quantity__lte=10
    )

    for item in low_stock_items:
        create_alert(
            alert_type="low_stock",
            title=f"Low stock: {item.product.name}",
            message=(
                f"{item.product.name} has fallen to "
                f"{item.quantity} units at "
                f"{item.warehouse.name}."
            ),
            severity="warning",
            department="inventory",
            source_model="Inventory",
            source_object_id=item.id,
            metadata={
                "quantity": item.quantity,
                "reorder_level": 10,
                "warehouse": item.warehouse.name,
            },
        )

    return render(
        request,
        "inventory/inventory_list.html",
        {
            "inventory_records": inventory_records,
            "warehouses": warehouses,
            "query": query,
            "selected_warehouse": warehouse_id,
            "selected_status": stock_status,
        },
    )


@login_required
@department_required("inventory")
@role_required("officer")
def inventory_create(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Inventory record created successfully.",
            )
            return redirect("inventory_list")
    else:
        form = InventoryForm()

    return render(
        request,
        "inventory/inventory_form.html",
        {
            "form": form,
            "page_title": "Add Inventory Record",
        },
    )


@login_required
@department_required("inventory")
@role_required("officer")
def inventory_update(request, inventory_id):
    inventory = get_object_or_404(
        Inventory,
        id=inventory_id,
    )

    if request.method == "POST":
        form = InventoryForm(
            request.POST,
            instance=inventory,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Inventory record updated successfully.",
            )
            return redirect("inventory_list")
    else:
        form = InventoryForm(instance=inventory)

    return render(
        request,
        "inventory/inventory_form.html",
        {
            "form": form,
            "page_title": "Edit Inventory Record",
        },
    )


@login_required
@department_required("inventory")
@role_required("officer")
def stock_movement_create(request, inventory_id):
    inventory = get_object_or_404(
        Inventory,
        id=inventory_id,
    )

    if request.method == "POST":
        form = StockMovementForm(request.POST)

        if form.is_valid():
            movement = form.save(commit=False)
            movement.inventory = inventory
            movement.created_by = request.user

            if movement.movement_type == "stock_in":
                inventory.quantity += movement.quantity

            elif movement.movement_type == "stock_out":
                if movement.quantity > inventory.quantity:
                    form.add_error(
                        "quantity",
                        "Stock-out quantity cannot exceed available stock.",
                    )

                    return render(
                        request,
                        "inventory/stock_movement_form.html",
                        {
                            "form": form,
                            "inventory": inventory,
                        },
                    )

                inventory.quantity -= movement.quantity

            elif movement.movement_type == "adjustment":
                inventory.quantity = movement.quantity

            inventory.save()
            movement.save()

            messages.success(
                request,
                "Stock movement recorded successfully.",
            )

            return redirect("inventory_list")
    else:
        form = StockMovementForm()

    return render(
        request,
        "inventory/stock_movement_form.html",
        {
            "form": form,
            "inventory": inventory,
        },
    )


@login_required
@department_required("inventory")
@role_required("viewer")
def stock_movement_list(request):
    movements = StockMovement.objects.select_related(
        "inventory__product",
        "inventory__warehouse",
        "created_by",
    )

    return render(
        request,
        "inventory/stock_movement_list.html",
        {"movements": movements},
    )

# Create your views here.
