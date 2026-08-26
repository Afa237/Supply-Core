from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
    )
from django.shortcuts import get_object_or_404, redirect, render
from warehouse.models import Warehouse
from accounts.decorators import (
    department_required,
    role_required,
)
from .forms import InventoryForm, StockMovementForm
from .models import Inventory, StockMovement
from notifications.services import (
    create_alert,
    resolve_inventory_alert,
)
from django.db import models
from django.db.models.functions import TruncMonth



@login_required
@department_required("inventory")
@role_required("viewer")
def inventory_list(request):
    inventory_records = Inventory.objects.select_related(
        "product",
        "warehouse",
    )
    inventory_value_data = (
        Inventory.objects
        .select_related("product")
        .annotate(
            calculated_value=ExpressionWrapper(
                F("quantity") * F("product__unit_price"),
                output_field=DecimalField(
                    max_digits=18,
                    decimal_places=2,
                ),
            )
        )
        .aggregate(
            total=Sum("calculated_value")
        )
    )

    total_inventory_value = (
        inventory_value_data["total"] or 0
    )
    
    stock_in_value_data = (
        StockMovement.objects
        .filter(movement_type="stock_in")
        .annotate(
            movement_value=ExpressionWrapper(
                F("quantity")
                * F("inventory__product__unit_price"),
                output_field=DecimalField(
                    max_digits=18,
                    decimal_places=2,
                ),
            )
        )
        .aggregate(
            total=Sum("movement_value")
        )
    )

    stock_in_value = (
        stock_in_value_data["total"]
        or 0
    )
    stock_out_value_data = (
        StockMovement.objects
        .filter(movement_type="stock_out")
        .annotate(
            movement_value=ExpressionWrapper(
                F("quantity")
                * F("inventory__product__unit_price"),
                output_field=DecimalField(
                    max_digits=18,
                    decimal_places=2,
                ),
            )
        )
        .aggregate(
            total=Sum("movement_value")
        )
    )

    stock_out_value = (
        stock_out_value_data["total"]
        or 0
    )
    current_units = (
        Inventory.objects.aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )
    warehouses = Warehouse.objects.all()

    warehouse_values = (
        Inventory.objects
        .values("warehouse__id", "warehouse__name")
        .annotate(
            total_value=Sum(
                ExpressionWrapper(
                    F("quantity") * F("product__unit_price"),
                    output_field=DecimalField(
                        max_digits=18,
                        decimal_places=2,
                    ),
                )
            )
        )
        .order_by("-total_value")
    )

    movement_data = (
        StockMovement.objects
        .annotate(month=TruncMonth("created_at"))
        .values("month", "movement_type")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("month")
    )
    movement_months = sorted(
        {item["month"] for item in movement_data if item["month"]}
    )
    movement_chart_labels = [
        month.strftime("%b %Y") for month in movement_months
    ]
    movement_chart_stock_in = [
        sum(
            item["total_quantity"]
            for item in movement_data
            if item["month"] == month
            and item["movement_type"] == "stock_in"
        )
        for month in movement_months
    ]
    movement_chart_stock_out = [
        sum(
            item["total_quantity"]
            for item in movement_data
            if item["month"] == month
            and item["movement_type"] == "stock_out"
        )
        for month in movement_months
    ]

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
        quantity__lte=F("product__reorder_level")
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
                "reorder_level": item.product.reorder_level,
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
            "total_inventory_value": total_inventory_value,
            "stock_in_value": stock_in_value,
            "stock_out_value": stock_out_value,
            "current_units": current_units,
            "warehouse_values": warehouse_values,
            "movement_chart_labels": movement_chart_labels,
            "movement_chart_stock_in": movement_chart_stock_in,
            "movement_chart_stock_out": movement_chart_stock_out,
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
@role_required("manager")
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
@role_required("manager")
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
            if inventory.quantity > inventory.product.reorder_level:
                resolve_inventory_alert(inventory)
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
