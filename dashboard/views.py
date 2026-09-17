from django.contrib.auth.decorators import login_required 
from django.db.models import Count, F 
from django.shortcuts import render
from accounts.models import Branch 
from audit.models import AuditLog 
from inventory.models import Inventory 
from logistics.models import Shipment, Driver, Vehicle 
from procurement.models import PurchaseOrder 
from products.models import Product 
from suppliers.models import Supplier 
from warehouse.models import Warehouse


@login_required
def home(request):
    user = request.user
    profile = getattr(user, "profile", None)

    is_full_access = (
        user.is_superuser
        or (
            profile
            and profile.role in [
                "admin",
                "supply_chain_manager",
            ]
        )
    )

    department = profile.department if profile else ""

# -------------------------------------------------
# DETERMINE AVAILABLE / SELECTED BRANCH
# -------------------------------------------------

    if user.is_superuser:
        available_branches = Branch.objects.filter(
            active=True
        ).select_related("company")

    elif profile and profile.company:
        available_branches = Branch.objects.filter(
            company=profile.company,
            active=True,
        ).select_related("company")

    else:
        available_branches = Branch.objects.none()

    selected_branch = None
    selected_branch_id = request.GET.get("branch", "")

    if is_full_access:
        if selected_branch_id:
            selected_branch = available_branches.filter(
                id=selected_branch_id
            ).first()
    else:
        selected_branch = profile.branch if profile else None

# -------------------------------------------------
# BASE QUERYSETS
# -------------------------------------------------

    purchase_orders = PurchaseOrder.objects.select_related(
        "supplier",
        "branch",
    )

    shipments = Shipment.objects.select_related(
        "destination_warehouse",
        "branch",
    )

    warehouses = Warehouse.objects.select_related(
        "branch",
    )

    inventory = Inventory.objects.select_related(
        "product",
        "warehouse",
        "warehouse__branch",
    )

    drivers = Driver.objects.select_related(
        "branch",
    )

    vehicles = Vehicle.objects.select_related(
        "branch",
    )

# -------------------------------------------------
# APPLY BRANCH SCOPE
# -------------------------------------------------

    if selected_branch:

        purchase_orders = purchase_orders.filter(
            branch=selected_branch
        )

        shipments = shipments.filter(
            branch=selected_branch
        )

        warehouses = warehouses.filter(
            branch=selected_branch
        )

        inventory = inventory.filter(
            warehouse__branch=selected_branch
        )

        drivers = drivers.filter(
            branch=selected_branch
        )

        vehicles = vehicles.filter(
            branch=selected_branch
        )

    elif not is_full_access:
        # A branch-level user without a branch sees nothing.
        purchase_orders = purchase_orders.none()
        shipments = shipments.none()
        warehouses = warehouses.none()
        inventory = inventory.none()
        drivers = drivers.none()
        vehicles = vehicles.none()

    elif profile and profile.company and not user.is_superuser:
    # Company-wide Admin / SCM Manager:
    # "All Branches" means all branches in THEIR company only.

        purchase_orders = purchase_orders.filter(
            branch__company=profile.company
        )

        shipments = shipments.filter(
            branch__company=profile.company
        )

        warehouses = warehouses.filter(
            branch__company=profile.company
        )

        inventory = inventory.filter(
            warehouse__branch__company=profile.company
        )

        drivers = drivers.filter(
            branch__company=profile.company
        )

        vehicles = vehicles.filter(
            branch__company=profile.company
        )

# -------------------------------------------------
# PRODUCTS / SUPPLIERS FOR CURRENT SCOPE
# -------------------------------------------------

    product_ids = inventory.values_list(
        "product_id",
        flat=True,
    ).distinct()

    supplier_ids = purchase_orders.values_list(
        "supplier_id",
        flat=True,
    ).distinct()

    scoped_products = Product.objects.filter(
        id__in=product_ids
    )
    scoped_suppliers = Supplier.objects.filter(
    id__in=supplier_ids
)

    # -------------------------------------------------
    # RECENT ACTIVITY
    # -------------------------------------------------

    recent_activity = AuditLog.objects.select_related(
        "user"
    )
    if selected_branch:
        recent_activity = recent_activity.filter(
            user__profile__branch=selected_branch
        )

    recent_activity = recent_activity[:8]
    
    
    # -------------------------------------------------
    # LOW STOCK FOR CURRENT BRANCH SCOPE
    # -------------------------------------------------
    
    low_stock = inventory.filter(
        quantity__lte=F("product__reorder_level")
    )

    # -------------------------------------------------
    # COMMON CONTEXT
    # -------------------------------------------------

    context = {
        "department": department,
        "is_full_access": is_full_access,
        "available_branches": available_branches,
        "selected_branch": selected_branch,
        "selected_branch_id": selected_branch_id,
        "recent_activity": recent_activity,
    }

# -------------------------------------------------
# ADMIN / SUPPLY CHAIN MANAGER
# -------------------------------------------------

    if is_full_access:

        low_stock = inventory.filter(
            quantity__lte=F("product__reorder_level")
        )

        context.update({

            "total_products":
                scoped_products.count(),

            "total_suppliers":
                scoped_suppliers.count(),

            "total_purchase_orders":
                purchase_orders.count(),

            "total_shipments":
                shipments.count(),

            "total_warehouses":
                warehouses.count(),

            "low_stock_count":
                low_stock.count(),

            "in_transit_shipments":
                shipments.filter(
                    status="in_transit"
                ).count(),

            "delayed_shipments":
                shipments.filter(
                    status="delayed"
                ).count(),
        })

    # Inventory chart

    low_stock_total = low_stock.count()

    healthy_stock_total = (
        inventory.count()
        - low_stock_total
    )

    context["inventory_chart_labels"] = [
        "Healthy Stock",
        "Low Stock",
    ]

    context["inventory_chart_data"] = [
        healthy_stock_total,
        low_stock_total,
    ]

    # Shipment chart

    shipment_status_data = (
        shipments
        .values("status")
        .annotate(total=Count("id"))
        .order_by()
    )

    context["shipment_chart_labels"] = [
        item["status"].replace("_", " ").title()
        for item in shipment_status_data
    ]

    context["shipment_chart_data"] = [
        item["total"]
        for item in shipment_status_data
    ]

    # Procurement chart

    po_status_data = (
        purchase_orders
        .values("status")
        .annotate(total=Count("id"))
        .order_by()
    )

    context["po_chart_labels"] = [
        item["status"].replace("_", " ").title()
        for item in po_status_data
    ]

    context["po_chart_data"] = [
        item["total"]
        for item in po_status_data
    ]

    # -------------------------------------------------
    # PROCUREMENT
    # -------------------------------------------------

    if department == "procurement":

        context.update({

            "total_purchase_orders":
                purchase_orders.count(),

            "pending_purchase_orders":
                purchase_orders.filter(
                    status="pending"
                ).count(),

            "total_suppliers":
                scoped_suppliers.count(),

            "total_products":
                scoped_products.count(),

            "recent_purchase_orders":
                purchase_orders.order_by(
                    "-created_at"
                )[:5],
        })

    # -------------------------------------------------
    # LOGISTICS
    # -------------------------------------------------

    elif department == "logistics":

        context.update({

            "total_shipments":
                shipments.count(),

            "in_transit_shipments":
                shipments.filter(
                    status="in_transit"
                ).count(),

            "delayed_shipments":
                shipments.filter(
                    status="delayed"
                ).count(),

            "delivered_shipments":
                shipments.filter(
                    status="delivered"
                ).count(),

            "total_drivers":
                drivers.count(),
            
            "total_vehicles":
                vehicles.count(),

            "recent_shipments":
                shipments.order_by(
                    "-created_at"
                )[:5],
        })

    # -------------------------------------------------
    # INVENTORY
    # -------------------------------------------------

    elif department == "inventory":

        context.update({

            "inventory_records":
                inventory.count(),

            "low_stock_count":
                inventory.filter(
                    quantity__lte=F(
                        "product__reorder_level"
                    )
                ).count(),

            "total_products":
                scoped_products.count(),

            "total_warehouses":
                warehouses.count(),
        })

    # -------------------------------------------------
    # WAREHOUSE
    # -------------------------------------------------

    elif department == "warehouse":

        context.update({
        
            "total_warehouses":
                warehouses.count(),
            
            "inventory_records":
                inventory.count(),
            
            "low_stock_count":
                inventory.filter(
                    quantity__lte=F(
                        "product__reorder_level"
                    )
                ).count(),
        })
    return render(
    request,
    "dashboard/index.html",
    context,
)