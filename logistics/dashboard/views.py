from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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

    department = (
        profile.department
        if profile
        else ""
    )

    context = {
        "department": department,
        "is_full_access": is_full_access,
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
