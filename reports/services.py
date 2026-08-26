from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Sum,
)

from customers.models import CustomerTransaction
from inventory.models import Inventory, StockMovement
from logistics.models import Shipment
from procurement.models import PurchaseOrder


def get_report_data(
    date_from="",
    date_to="",
):

    # ======================================
    # BASE QUERYSETS
    # ======================================

    purchase_orders = PurchaseOrder.objects.all()

    shipments = Shipment.objects.all()

    stock_movements = StockMovement.objects.all()

    customer_transactions = (
        CustomerTransaction.objects.select_related(
            "customer",
            "inventory__product",
        )
    )


    # ======================================
    # DATE FILTERING
    # ======================================

    if date_from:

        purchase_orders = purchase_orders.filter(
            order_date__gte=date_from
        )

        shipments = shipments.filter(
            created_at__date__gte=date_from
        )

        stock_movements = stock_movements.filter(
            created_at__date__gte=date_from
        )

        customer_transactions = (
            customer_transactions.filter(
                created_at__date__gte=date_from
            )
        )


    if date_to:

        purchase_orders = purchase_orders.filter(
            order_date__lte=date_to
        )

        shipments = shipments.filter(
            created_at__date__lte=date_to
        )

        stock_movements = stock_movements.filter(
            created_at__date__lte=date_to
        )

        customer_transactions = (
            customer_transactions.filter(
                created_at__date__lte=date_to
            )
        )


    # ======================================
    # CURRENT INVENTORY VALUE
    # ======================================

    current_inventory_value = (
        Inventory.objects
        .annotate(
            value=ExpressionWrapper(
                F("quantity")
                * F("product__unit_price"),
                output_field=DecimalField(
                    max_digits=18,
                    decimal_places=2,
                ),
            )
        )
        .aggregate(
            total=Sum("value")
        )["total"]
        or 0
    )


    # ======================================
    # STOCK RECEIVED VALUE
    # ======================================

    stock_in_value = (
        stock_movements
        .filter(
            movement_type="stock_in"
        )
        .annotate(
            value=ExpressionWrapper(
                F("quantity")
                * F(
                    "inventory__product__unit_price"
                ),
                output_field=DecimalField(
                    max_digits=18,
                    decimal_places=2,
                ),
            )
        )
        .aggregate(
            total=Sum("value")
        )["total"]
        or 0
    )


    # ======================================
    # STOCK ISSUED VALUE
    # ======================================

    stock_out_value = (
        stock_movements
        .filter(
            movement_type="stock_out"
        )
        .annotate(
            value=ExpressionWrapper(
                F("quantity")
                * F(
                    "inventory__product__unit_price"
                ),
                output_field=DecimalField(
                    max_digits=18,
                    decimal_places=2,
                ),
            )
        )
        .aggregate(
            total=Sum("value")
        )["total"]
        or 0
    )


    # ======================================
    # PROCUREMENT
    # ======================================

    po_total = purchase_orders.count()

    po_value = (
        purchase_orders.aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )


    po_status_data = (
        purchase_orders
        .values("status")
        .annotate(
            total=Count("id")
        )
        .order_by()
    )


    po_chart_labels = [
        item["status"]
        .replace("_", " ")
        .title()

        for item in po_status_data
    ]


    po_chart_data = [
        item["total"]
        for item in po_status_data
    ]


    # ======================================
    # LOGISTICS
    # ======================================

    shipment_total = shipments.count()


    delivered_shipments = (
        shipments.filter(
            status="delivered"
        ).count()
    )


    delayed_shipments = (
        shipments.filter(
            status="delayed"
        ).count()
    )


    in_transit_shipments = (
        shipments.filter(
            status="in_transit"
        ).count()
    )


    shipment_status_data = (
        shipments
        .values("status")
        .annotate(
            total=Count("id")
        )
        .order_by()
    )


    shipment_chart_labels = [
        item["status"]
        .replace("_", " ")
        .title()

        for item in shipment_status_data
    ]


    shipment_chart_data = [
        item["total"]
        for item in shipment_status_data
    ]


    # ======================================
    # CUSTOMER PERFORMANCE
    # ======================================

    total_customer_dispatches = (
        customer_transactions.count()
    )


    total_quantity_supplied = (
        customer_transactions
        .aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )


    top_customers = (
        customer_transactions
        .values(
            "customer__id",
            "customer__name",
        )
        .annotate(
            total_quantity=Sum(
                "quantity"
            ),
            transaction_count=Count(
                "id"
            ),
        )
        .order_by(
            "-total_quantity"
        )[:5]
    )


    # ======================================
    # LOW STOCK
    # ======================================

    low_stock_count = (
        Inventory.objects.filter(
            quantity__lte=F(
                "product__reorder_level"
            )
        ).count()
    )


    # ======================================
    # RETURN REPORT DATA
    # ======================================

    return {

        "date_from":
            date_from,

        "date_to":
            date_to,

        "current_inventory_value":
            current_inventory_value,

        "stock_in_value":
            stock_in_value,

        "stock_out_value":
            stock_out_value,

        "low_stock_count":
            low_stock_count,

        "po_total":
            po_total,

        "po_value":
            po_value,

        "po_chart_labels":
            po_chart_labels,

        "po_chart_data":
            po_chart_data,

        "shipment_total":
            shipment_total,

        "delivered_shipments":
            delivered_shipments,

        "delayed_shipments":
            delayed_shipments,

        "in_transit_shipments":
            in_transit_shipments,

        "shipment_chart_labels":
            shipment_chart_labels,

        "shipment_chart_data":
            shipment_chart_data,

        "total_customer_dispatches":
            total_customer_dispatches,

        "total_quantity_supplied":
            total_quantity_supplied,

        "top_customers":
            top_customers,
    }