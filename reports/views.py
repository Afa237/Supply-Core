from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from .services import get_report_data
import csv
from django.utils import timezone


@login_required
def reports_dashboard(request):

    date_from = request.GET.get(
        "date_from",
        "",
    )

    date_to = request.GET.get(
        "date_to",
        "",
    )

    context = get_report_data(
        date_from=date_from,
        date_to=date_to,
    )

    return render(
        request,
        "reports/reports_dashboard.html",
        context,
    )
@login_required
def export_csv(request):

    date_from = request.GET.get(
        "date_from",
        "",
    )

    date_to = request.GET.get(
        "date_to",
        "",
    )

    report_data = get_report_data(
        date_from=date_from,
        date_to=date_to,
    )

    response = HttpResponse(
        content_type="text/csv"
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; '
        'filename="supply_core_management_report.csv"'
    )

    writer = csv.writer(response)

    # TITLE
    writer.writerow([
        "SUPPLY CORE",
    ])

    writer.writerow([
        "Management Operations Report",
    ])

    writer.writerow([
        "Date From",
        date_from or "Beginning",
    ])

    writer.writerow([
        "Date To",
        date_to or "Present",
    ])

    writer.writerow([])


    # EXECUTIVE SUMMARY
    writer.writerow([
        "EXECUTIVE SUMMARY"
    ])

    writer.writerow([
        "Metric",
        "Value",
    ])

    writer.writerow([
        "Current Inventory Value",
        report_data[
            "current_inventory_value"
        ],
    ])

    writer.writerow([
        "Stock Received Value",
        report_data[
            "stock_in_value"
        ],
    ])

    writer.writerow([
        "Stock Issued Value",
        report_data[
            "stock_out_value"
        ],
    ])

    writer.writerow([
        "Low Stock Items",
        report_data[
            "low_stock_count"
        ],
    ])

    writer.writerow([])


    # PROCUREMENT
    writer.writerow([
        "PROCUREMENT"
    ])

    writer.writerow([
        "Purchase Orders",
        report_data[
            "po_total"
        ],
    ])

    writer.writerow([
        "Procurement Value",
        report_data[
            "po_value"
        ],
    ])

    writer.writerow([])

    writer.writerow([
        "Purchase Order Status",
        "Total",
    ])

    for label, total in zip(
        report_data[
            "po_chart_labels"
        ],
        report_data[
            "po_chart_data"
        ],
    ):

        writer.writerow([
            label,
            total,
        ])


    writer.writerow([])


    # LOGISTICS
    writer.writerow([
        "LOGISTICS"
    ])

    writer.writerow([
        "Total Shipments",
        report_data[
            "shipment_total"
        ],
    ])

    writer.writerow([
        "Delivered",
        report_data[
            "delivered_shipments"
        ],
    ])

    writer.writerow([
        "In Transit",
        report_data[
            "in_transit_shipments"
        ],
    ])

    writer.writerow([
        "Delayed",
        report_data[
            "delayed_shipments"
        ],
    ])

    writer.writerow([])

    writer.writerow([
        "Shipment Status",
        "Total",
    ])

    for label, total in zip(
        report_data[
            "shipment_chart_labels"
        ],
        report_data[
            "shipment_chart_data"
        ],
    ):

        writer.writerow([
            label,
            total,
        ])


    writer.writerow([])


    # CUSTOMER PERFORMANCE
    writer.writerow([
        "CUSTOMER PERFORMANCE"
    ])

    writer.writerow([
        "Customer Dispatches",
        report_data[
            "total_customer_dispatches"
        ],
    ])

    writer.writerow([
        "Quantity Supplied",
        report_data[
            "total_quantity_supplied"
        ],
    ])

    writer.writerow([])

    writer.writerow([
        "Top Customers"
    ])

    writer.writerow([
        "Customer",
        "Transactions",
        "Quantity Supplied",
    ])

    for customer in report_data[
        "top_customers"
    ]:

        writer.writerow([
            customer[
                "customer__name"
            ],

            customer[
                "transaction_count"
            ],

            customer[
                "total_quantity"
            ],
        ])


    return response
@login_required 
def export_pdf(request):
    date_from = request.GET.get(
        "date_from",
        "",
    )

    date_to = request.GET.get(
        "date_to",
        "",
    )

    report_data = get_report_data(
        date_from=date_from,
        date_to=date_to,
    )

    report_data["generated_at"] = (
        timezone.localtime()
    )

    report_data["generated_by"] = (
        request.user
    )

    return render(
        request,
        "reports/report_pdf.html",
        report_data,
    )