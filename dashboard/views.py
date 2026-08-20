from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from inventory.models import Inventory
from logistics.models import Shipment, Driver, Vehicle
from procurement.models import PurchaseOrder
from products.models import Product
from suppliers.models import Supplier
from warehouse.models import Warehouse
from django.db.models import Count

from audit.models import AuditLog
from inventory.models import Inventory
from logistics.models import Shipment
from procurement.models import PurchaseOrder


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

    department = (
        profile.department
        if profile
        else ""
    )
    recent_activity = AuditLog.objects.select_related(
        "user"
    ).all()[:8]

    context = {
        "department": department,
        "is_full_access": is_full_access,
        "recent_activity": recent_activity,
    }


    # ADMIN / SUPPLY CHAIN MANAGER

    if is_full_access:

        context.update({

            "total_products":
                Product.objects.count(),

            "total_suppliers":
                Supplier.objects.count(),

            "total_purchase_orders":
                PurchaseOrder.objects.count(),

            "total_shipments":
                Shipment.objects.count(),

            "total_warehouses":
                Warehouse.objects.count(),

            "low_stock_count":
                Inventory.objects.filter(
                    quantity__lte=10
                ).count(),

            "in_transit_shipments":
                Shipment.objects.filter(
                    status="in_transit"
                ).count(),

            "delayed_shipments":
                Shipment.objects.filter(
                    status="delayed"
                ).count(),

        })
        
        # Inventory chart
        low_stock_total = Inventory.objects.filter(
            quantity__lte=10
        ).count()

        healthy_stock_total = (
            Inventory.objects.count()
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
            Shipment.objects.values("status")
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
            PurchaseOrder.objects.values("status")
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


    # PROCUREMENT

    elif department == "procurement":

        context.update({

            "total_purchase_orders":
                PurchaseOrder.objects.count(),

            "pending_purchase_orders":
                PurchaseOrder.objects.filter(
                    status="pending"
                ).count(),

            "total_suppliers":
                Supplier.objects.count(),

            "total_products":
                Product.objects.count(),

            "recent_purchase_orders":
                PurchaseOrder.objects.select_related(
                    "supplier"
                )[:5],

        })


    # LOGISTICS

    elif department == "logistics":

        context.update({

            "total_shipments":
                Shipment.objects.count(),

            "in_transit_shipments":
                Shipment.objects.filter(
                    status="in_transit"
                ).count(),

            "delayed_shipments":
                Shipment.objects.filter(
                    status="delayed"
                ).count(),

            "delivered_shipments":
                Shipment.objects.filter(
                    status="delivered"
                ).count(),

            "total_drivers":
                Driver.objects.count(),

            "total_vehicles":
                Vehicle.objects.count(),

            "recent_shipments":
                Shipment.objects.select_related(
                    "destination_warehouse"
                )[:5],

        })


    # INVENTORY

    elif department == "inventory":

        context.update({

            "inventory_records":
                Inventory.objects.count(),

            "low_stock_count":
                Inventory.objects.filter(
                    quantity__lte=10
                ).count(),

            "total_products":
                Product.objects.count(),

            "total_warehouses":
                Warehouse.objects.count(),

        })


    # WAREHOUSE

    elif department == "warehouse":

        context.update({

            "total_warehouses":
                Warehouse.objects.count(),

            "inventory_records":
                Inventory.objects.count(),

            "low_stock_count":
                Inventory.objects.filter(
                    quantity__lte=10
                ).count(),})


    return render(
        request,
        "dashboard/index.html",
        context,
    )
# Create your views here.
