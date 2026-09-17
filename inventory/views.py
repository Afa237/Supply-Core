from django.contrib import messages 
from django.contrib.auth.decorators import login_required 
from django.db.models import ( DecimalField, ExpressionWrapper, F, Q, Sum, ) 
from django.db.models.functions import TruncMonth 
from django.shortcuts import get_object_or_404, redirect, render 
from django.http import HttpResponse
import csv
from warehouse.models import Warehouse
from accounts.decorators import ( department_required, role_required, ) 
from accounts.access import filter_by_user_scope
from .forms import InventoryForm, StockMovementForm 
from .models import Inventory, StockMovement
from notifications.services import ( create_alert, resolve_inventory_alert, )

# =========================================================
# INVENTORY LIST
# =========================================================

@login_required 
@department_required("inventory") 
@role_required("viewer") 
def inventory_list(request):
    # -----------------------------------------------------
    # BRANCH-SCOPED INVENTORY
    # -----------------------------------------------------

    inventory_records = Inventory.objects.select_related(
        "product",
        "warehouse",
        "warehouse__branch",
        "warehouse__branch__company",
    )

    inventory_records = filter_by_user_scope(
        inventory_records,
        request.user,
        branch_field="warehouse__branch",
    )

    # Separate scoped queryset for KPI calculations
    scoped_inventory = Inventory.objects.select_related(
        "product",
        "warehouse",
        "warehouse__branch",
        "warehouse__branch__company",
    )

    scoped_inventory = filter_by_user_scope(
        scoped_inventory,
        request.user,
        branch_field="warehouse__branch",
    )

    # -----------------------------------------------------
    # CURRENT INVENTORY VALUE
    # -----------------------------------------------------

    inventory_value_data = (
        scoped_inventory
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

    # -----------------------------------------------------
    # STOCK-IN VALUE
    # -----------------------------------------------------

    scoped_movements = filter_by_user_scope(
        StockMovement.objects.select_related(
            "inventory__product",
            "inventory__warehouse",
            "inventory__warehouse__branch",
        ),
        request.user,
        branch_field="inventory__warehouse__branch",
    )

    stock_in_value_data = (
        scoped_movements
        .filter(
            movement_type="stock_in"
        )
        .annotate(
            movement_value=ExpressionWrapper(
                F("quantity")
                * F("inventory__product__unit_price"),
                output_field=DecimalField(
                    max_digits=18,
                    decimal_places=2,
                ),
            ),
        )
        .aggregate(
            total=Sum("movement_value")
        )
    )

    stock_in_value = (
        stock_in_value_data["total"] or 0
    )

    # -----------------------------------------------------
    # STOCK-OUT VALUE
    # -----------------------------------------------------

    stock_out_value_data = (
        scoped_movements
        .filter(
            movement_type="stock_out"
        )
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
        stock_out_value_data["total"] or 0
    )

    current_units = (
        scoped_inventory.aggregate(total=Sum("quantity"))["total"] or 0
    )

    warehouses = filter_by_user_scope(
        Warehouse.objects.all(),
        request.user,
    ).order_by("name")
    
    warehouse_values = (
        scoped_inventory.values(
            "warehouse__id",
            "warehouse__name",
        )
        .annotate(
            total_value=Sum(
                ExpressionWrapper(
                    F("quantity")
                    * F("product__unit_price"),
                    output_field=DecimalField(
                        max_digits=18,
                        decimal_places=2,
                    )
                )
            )
        ).order_by("-total_value")
    )
    # -----------------------------------------------------

    # INVENTORY MOVEMENT CHART

    # -----------------------------------------------------

    movement_data = (

        scoped_movements

        .annotate(

            month=TruncMonth("created_at")

        )

        .values(

            "month",

            "movement_type",

        )

        .annotate(

            total_quantity=Sum("quantity")

        )

        .order_by("month")

    )

    movement_months = sorted(

        {

            item["month"]

            for item in movement_data

            if item["month"]

        }

    )

    movement_chart_labels = [

        month.strftime("%b %Y")

        for month in movement_months

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

    # -----------------------------------------------------

    # FILTERS

    # -----------------------------------------------------

    query = request.GET.get(

        "q",

        "",

    ).strip()

    warehouse_id = request.GET.get(

        "warehouse",

        "",

    )

    stock_status = request.GET.get(

        "status",

        "",

    )

    if query:

        inventory_records = inventory_records.filter(

            Q(

                product__name__icontains=query

            )

            | Q(

                product__sku__icontains=query

            )

            | Q(

                warehouse__name__icontains=query

            )

            | Q(

                warehouse__branch__name__icontains=query

            )

        )

    if warehouse_id:

        inventory_records = inventory_records.filter(

            warehouse_id=warehouse_id

        )

    if stock_status == "low":

        inventory_records = inventory_records.filter(

            quantity__lte=F(

                "product__reorder_level"

            )

        )

    # -----------------------------------------------------

    # LOW-STOCK ALERTS

    # -----------------------------------------------------

    low_stock_items = scoped_inventory.filter(

        quantity__lte=F(

            "product__reorder_level"

        )

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

                "reorder_level":

                    item.product.reorder_level,

                "warehouse":

                    item.warehouse.name,

                "branch": (

                    item.warehouse.branch.name

                    if item.warehouse.branch

                    else ""

                ),

            },

        )

    # -----------------------------------------------------

    # PAGE

    # -----------------------------------------------------

    return render(

        request,

        "inventory/inventory_list.html",

        {

            "inventory_records":

                inventory_records,

            "warehouses":

                warehouses,

            "query":

                query,

            "selected_warehouse":

                warehouse_id,

            "selected_status":

                stock_status,"total_inventory_value":

                total_inventory_value,

            "stock_in_value":

                stock_in_value,

            "stock_out_value":

                stock_out_value,

            "current_units":

                current_units,

            "warehouse_values":

                warehouse_values,

            "movement_chart_labels":

                movement_chart_labels,

            "movement_chart_stock_in":

                movement_chart_stock_in,

            "movement_chart_stock_out":

                movement_chart_stock_out,

        },

    )



# =========================================================
# CREATE INVENTORY
# =========================================================

@login_required 
@department_required("inventory") 
@role_required("officer") 
def inventory_create(request):
    if request.method == "POST":

        form = InventoryForm(request.POST, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, "Inventory record created successfully.")

            return redirect("inventory_list")

    else:
        form = InventoryForm(user=request.user)

    return render(request, "inventory/inventory_form.html", {
        "form": form,
        "page_title": "Add Inventory Record",
    })


@login_required
@department_required("inventory")
@role_required("officer")
def inventory_update(request, inventory_id):
    inventory_records = Inventory.objects.select_related(
        "product", "warehouse", "warehouse__branch"
    )

    inventory_records = filter_by_user_scope(
        inventory_records, request.user, branch_field="warehouse__branch"
    )

    inventory = get_object_or_404(inventory_records, id=inventory_id)

    if request.method == "POST":

        form = InventoryForm(request.POST, instance=inventory, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, "Inventory record updated successfully.")

            return redirect("inventory_list")

    else:
        form = InventoryForm(instance=inventory, user=request.user)

    return render(request, "inventory/inventory_form.html", {
        "form": form,
        "page_title": "Edit Inventory Record",
    })

#  CREATE STOCK MOVEMENT

@login_required 
@department_required("inventory") 
@role_required("manager") 
def stock_movement_create( request, inventory_id, ):
    inventory_records = Inventory.objects.select_related(
        "product", "warehouse", "warehouse__branch"
    )
    inventory_records = filter_by_user_scope(
        inventory_records, request.user, branch_field="warehouse__branch"
    )

    inventory = get_object_or_404(inventory_records, id=inventory_id)

    if request.method == "POST":
        form = StockMovementForm(request.POST)

        if form.is_valid():
            movement = form.save(commit=False)
            movement.inventory = inventory
            movement.created_by = request.user

        # ---------------------------------------------
        # STOCK IN
        # ---------------------------------------------

            if movement.movement_type == "stock_in":
                inventory.quantity += movement.quantity

        # ---------------------------------------------
        # STOCK OUT
        # ---------------------------------------------

            elif movement.movement_type == "stock_out":
                if movement.quantity > inventory.quantity:
                    form.add_error(
                        "quantity",
                        "Stock-out quantity cannot exceed available stock.",
                    )
                    return render(
                        request,
                        "inventory/stock_movement_form.html",
                        {"form": form, "inventory": inventory},
                    )
                inventory.quantity -= movement.quantity

        # ---------------------------------------------
        # ADJUSTMENT
        # ---------------------------------------------

            elif movement.movement_type == "adjustment":
                inventory.quantity = movement.quantity

            inventory.save()

        # Resolve existing low-stock alert
        # when inventory becomes healthy again.

            if inventory.quantity > inventory.product.reorder_level:
                resolve_inventory_alert(inventory)

            movement.save()

            messages.success(request, "Stock movement recorded successfully.")

            return redirect("inventory_list")

    else:
        form = StockMovementForm()

    return render(
        request,
        "inventory/stock_movement_form.html",
        {"form": form, "inventory": inventory},
    )
# =========================================================
# STOCK MOVEMENT HISTORY
# =========================================================
@login_required 
@department_required("inventory") 
@role_required("viewer") 
def stock_movement_list(request):
    movements = (
        StockMovement.objects.select_related(
            "inventory__product",
            "inventory__warehouse",
            "inventory__warehouse__branch",
            "created_by",
        )
    )

    movements = filter_by_user_scope(
        movements,
        request.user,
        branch_field="inventory__warehouse__branch",
    ).order_by("-created_at")

    return render(
        request,
        "inventory/stock_movement_list.html",
        {"movements": movements},
    )


# =========================================================
# INVENTORY CSV EXPORT
# =========================================================
@login_required
@department_required("inventory")
@role_required("viewer")
def inventory_export_csv(request):
    inventory_records = Inventory.objects.select_related(
        "product",
        "warehouse",
        "warehouse__branch",
        "warehouse__branch__company",
    )

    inventory_records = filter_by_user_scope(
        inventory_records,
        request.user,
        branch_field="warehouse__branch",
    )

    response = HttpResponse(
        content_type="text/csv"
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; filename="inventory.csv"'
    )

    writer = csv.writer(
        response
    )

    writer.writerow([
        "Product",
        "SKU",
        "Company",
        "Branch",
        "Warehouse",
        "Quantity",
        "Unit Price",
        "Stock Value",
        "Reorder Level",
        "Status",
    ])

    for record in inventory_records:

        company_name = ""
        branch_name = ""

        if record.warehouse.branch:

            branch_name = (
                record.warehouse.branch.name
            )

            company_name = (
                record.warehouse
                .branch
                .company
                .name
            )

        writer.writerow([
            record.product.name,
            record.product.sku,
            company_name,
            branch_name,
            record.warehouse.name,
            record.quantity,
            record.product.unit_price,
            record.stock_value,
            record.product.reorder_level,
            (
                "Low Stock"
                if record.is_low_stock
                else "In Stock"),
        ])

    return response