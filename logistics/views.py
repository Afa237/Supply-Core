from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import (
    department_required,
    role_required,
)

from .forms import DriverForm, ShipmentForm, VehicleForm
from .models import Driver, Shipment, Vehicle
from inventory.models import Inventory,StockMovement
from audit.utils import log_action
from django.utils import timezone
from notifications.services import (
    create_alert,
    resolve_shipment_alert,
)
from warehouse.models import Warehouse
from procurement.models import PurchaseOrder
from notifications.models import Alert
import csv
from django.http import HttpResponse
from accounts.access import filter_by_user_scope


@login_required
@department_required("logistics")
@role_required("viewer")
def shipment_list(request):

    shipments = Shipment.objects.select_related(
        "purchase_order",
        "destination_warehouse",
        "driver",
        "vehicle",
        "branch",
        "branch__company",
    )
    
    shipments = filter_by_user_scope(
        shipments,
        request.user,
    )

    query = request.GET.get(
        "q",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    )

    driver_id = request.GET.get(
        "driver",
        "",
    )

    vehicle_id = request.GET.get(
        "vehicle",
        "",
    )

    warehouse_id = request.GET.get(
        "warehouse",
        "",
    )

    date_from = request.GET.get(
        "date_from",
        "",
    )

    date_to = request.GET.get(
        "date_to",
        "",
    )

    delayed_only = request.GET.get(
        "delayed",
        "",
    )


    # SEARCH
    if query:

        shipments = shipments.filter(
            Q(
                tracking_number__icontains=query
            )
            | Q(
                purchase_order__po_number__icontains=query
            )
            | Q(
                origin__icontains=query
            )
            | Q(
                destination_warehouse__name__icontains=query
            )
            | Q(
                driver__name__icontains=query
            )
            | Q(
                vehicle__registration_number__icontains=query
            )
        )


    # STATUS
    if status:

        shipments = shipments.filter(
            status=status
        )


    # DRIVER
    if driver_id:

        shipments = shipments.filter(
            driver_id=driver_id
        )


    # VEHICLE
    if vehicle_id:

        shipments = shipments.filter(
            vehicle_id=vehicle_id
        )


    # DESTINATION WAREHOUSE
    if warehouse_id:

        shipments = shipments.filter(
            destination_warehouse_id=warehouse_id
        )


    # EXPECTED DELIVERY DATE FROM
    if date_from:

        shipments = shipments.filter(
            estimated_delivery_date__gte=date_from
        )


    # EXPECTED DELIVERY DATE TO
    if date_to:

        shipments = shipments.filter(
            estimated_delivery_date__lte=date_to
        )


    today = timezone.localdate()


    # DELAYED ONLY FILTER
    if delayed_only == "yes":

        shipments = shipments.filter(
            estimated_delivery_date__lt=today
        ).exclude(
            status__in=[
                "delivered",
                "cancelled",
            ]
        )


    # CREATE DELAY ALERTS
    delayed_shipments = Shipment.objects.filter(
        estimated_delivery_date__lt=today
    ).exclude(
        status__in=[
            "delivered",
            "cancelled",
        ]
    )

    for shipment in delayed_shipments:

        create_alert(
            alert_type="shipment_delay",
            title=(
                f"Delayed shipment: "
                f"{shipment.tracking_number}"
            ),
            message=(
                f"Shipment "
                f"{shipment.tracking_number} "
                f"was expected on "
                f"{shipment.estimated_delivery_date} "
                f"but has not been delivered."
            ),
            severity="critical",
            department="logistics",
            source_model="Shipment",
            source_object_id=shipment.id,
            metadata={
                "tracking_number":
                    shipment.tracking_number,

                "expected_delivery":
                    str(
                        shipment.estimated_delivery_date
                    ),

                "status":
                    shipment.status,
            },
        )


    drivers = Driver.objects.filter(
        active=True
    ).order_by("name")

    vehicles = Vehicle.objects.filter(
        active=True
    ).order_by(
        "registration_number"
    )

    warehouses = Warehouse.objects.all().order_by(
        "name"
    )


    return render(
        request,
        "logistics/shipment_list.html",
        {
            "shipments": shipments,

            "query":query,

            "selected_status":
                status,

            "selected_driver":
                driver_id,

            "selected_vehicle":
                vehicle_id,

            "selected_warehouse":
                warehouse_id,

            "selected_date_from":
                date_from,

            "selected_date_to":
                date_to,

            "selected_delayed":
                delayed_only,

            "status_choices":
                Shipment.STATUS_CHOICES,

            "drivers":
                drivers,

            "vehicles":
                vehicles,

            "warehouses":
                warehouses,
        },
    )


@login_required 
@department_required("logistics") 
@role_required("officer") 
def shipment_create(request):
    po_id = request.GET.get(
        "po"
    )

    initial_data = {}

    if po_id:

        purchase_order = get_object_or_404(
            PurchaseOrder,
            id=po_id,
        )

        initial_data[
            "purchase_order"
        ] = purchase_order


    if request.method == "POST":

        form = ShipmentForm(
            request.POST
        )

        if form.is_valid():
            existing_shipment = Shipment.objects.filter(
                purchase_order=form.cleaned_data["purchase_order"]
            ).exists()

            if existing_shipment:
                form.add_error(
                    "purchase_order",
                    (
                        "A shipment already exists "
                        "for this purchase order."
                    ),
                )
            else:
                shipment = form.save(
                    commit=False
                )

                shipment.created_by = (
                    request.user
                )
                profile = request.user.profile

                if profile.branch:
                    shipment.branch = profile.branch
                else:
                    messages.error(
                        request,
                        "Your account must be assigned to a branch before creating a shipment.",
                    )
                    return redirect("shipment_list")

                shipment.save()
                Alert.objects.filter(
                    alert_type="procurement_handoff",
                    source_model="PurchaseOrder",
                    source_object_id=str(
                        shipment.purchase_order.id
                    ),
                ).exclude(
                    status="resolved"
                ).update(
                    status="resolved",
                    resolved_at=timezone.now(),
                )
                log_action(
                    request,
                    action="create",
                    obj=shipment,
                    description=(
                        "Created shipment."
                    ),
                    metadata={
                        "purchase_order": shipment.purchase_order.po_number,
                    },
                )

                messages.success(
                    request,
                    "Shipment created successfully.",
                )

                return redirect(
                    "shipment_list"
                )

    else:

        form = ShipmentForm(
            initial=initial_data
        )


    return render(
        request,
        "logistics/shipment_form.html",
        {
            "form": form,
            "page_title":
                "Create Shipment",
        },
    )


@login_required
@department_required("logistics")
@role_required("officer")
def shipment_update(request, shipment_id):
    shipments = filter_by_user_scope(
    Shipment.objects.all(),
    request.user,
    )
    shipment = get_object_or_404(
        shipments,
        id=shipment_id,
    )

    if request.method == "POST":
        form = ShipmentForm(
            request.POST,
            instance=shipment,
        )

        if form.is_valid():
            shipment = form.save()
            if shipment.status in ["delivered", "cancelled"]:
                resolve_shipment_alert(shipment)
            log_action(
                request,
                action="update",
                obj=shipment,
                description="Updated shipment.",
            )

            messages.success(
                request,
                "Shipment updated successfully.",
            )

            return redirect("shipment_list")
    else:
        form = ShipmentForm(instance=shipment)

    return render(
        request,
        "logistics/shipment_form.html",
        {
            "form": form,
            "page_title": "Edit Shipment",
        },
    )


@login_required
@department_required("logistics")
@role_required("viewer")
def shipment_detail(request, shipment_id):
    shipments = filter_by_user_scope(
        Shipment.objects.all(),
        request.user,
    )
    shipment = get_object_or_404(
        Shipment.objects.select_related(
            "purchase_order",
            "destination_warehouse",
            "driver",
            "vehicle",
            "created_by",
            "branch",
        ),
        shipments,
        id=shipment_id,
    )

    return render(
        request,
        "logistics/shipment_detail.html",
        {"shipment": shipment},
    )


@login_required
@department_required("logistics")
@role_required("admin")
def shipment_delete(request, shipment_id):
    shipments = filter_by_user_scope(
    Shipment.objects.all(),
    request.user,
    )
    shipment = get_object_or_404(
        Shipment,
        id=shipment_id,
    )

    if request.method == "POST":
        log_action(
            request,
            action="delete",
            obj=shipment,
            description="deleted shipment.",
        )
        shipment.delete()

        messages.success(
            request,
            "Shipment deleted successfully.",
        )

        return redirect("shipment_list")

    return render(
        request,
        "logistics/shipment_confirm_delete.html",
        {"shipment": shipment},
    )


@login_required
@department_required("logistics")
@role_required("viewer")
def driver_list(request):
    drivers = Driver.objects.all()

    return render(
        request,
        "logistics/driver_list.html",
        {"drivers": drivers},
    )


@login_required
@department_required("logistics")
@role_required("officer")
def driver_create(request):
    if request.method == "POST":
        form = DriverForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("driver_list")
    else:
        form = DriverForm()

    return render(
        request,
        "logistics/simple_form.html",
        {
            "form": form,
            "page_title": "Add Driver",
            "cancel_url": "driver_list",},
    )


@login_required
@department_required("logistics")
@role_required("viewer")
def vehicle_list(request):
    vehicles = Vehicle.objects.all()

    return render(
        request,
        "logistics/vehicle_list.html",
        {"vehicles": vehicles},
    )


@login_required
@department_required("logistics")
@role_required("officer")
def vehicle_create(request):
    if request.method == "POST":
        form = VehicleForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("vehicle_list")
    else:
        form = VehicleForm()

    return render(
        request,
        "logistics/simple_form.html",
        {
            "form": form,
            "page_title": "Add Vehicle",
            "cancel_url": "vehicle_list",
        },
    )
@login_required
@department_required("logistics")
def receive_shipment(request, shipment_id):
    shipment = get_object_or_404(
        Shipment.objects.select_related(
            "purchase_order",
            "destination_warehouse",
        ),
        id=shipment_id,
    )

    if request.method == "POST":

        if shipment.status != "delivered":
            messages.error(
                request,
                "Shipment must be marked as Delivered before receiving stock.",
            )

            return redirect(
                "shipment_detail",
                shipment_id=shipment.id,
            )

        if shipment.inventory_received:
            messages.warning(
                request,
                "This shipment has already been received into inventory.",
            )

            return redirect(
                "shipment_detail",
                shipment_id=shipment.id,
            )

        for item in shipment.purchase_order.items.select_related("product"):

            inventory, created = Inventory.objects.get_or_create(
                product=item.product,
                warehouse=shipment.destination_warehouse,
                defaults={"quantity": 0},
            )

            inventory.quantity += item.quantity
            inventory.save()

            StockMovement.objects.create(
                inventory=inventory,
                movement_type="stock_in",
                quantity=item.quantity,
                reference=shipment.tracking_number,
                notes=f"Received from shipment {shipment.tracking_number}",
                created_by=request.user,
            )

        shipment.inventory_received = True
        shipment.save(update_fields=["inventory_received"])
        log_action(
            request,
            action="receive",
            obj=shipment,
            description="Received shipment into inventory.",
        )

        messages.success(
            request,
            "Shipment received and inventory updated successfully.",
        )

        return redirect(
            "shipment_detail",
            shipment_id=shipment.id,
        )

    return redirect(
        "shipment_detail",
        shipment_id=shipment.id,
    )
@login_required
@department_required("logistics")
@role_required("viewer")
def shipment_export_csv(request):
    shipments = Shipment.objects.select_related(
        "purchase_order",
        "destination_warehouse",
        "driver",
        "vehicle",
        "branch",
        "branch__company",
    )
    
    shipments = filter_by_user_scope(
        shipments,
        request.user,
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="shipments.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "Tracking Number",
        "Purchase Order",
        "Destination",
        "Driver",
        "Vehicle",
        "Status",
        "Expected Delivery",
    ])

    for shipment in shipments:
        writer.writerow([
            shipment.tracking_number,
            shipment.purchase_order.po_number,
            shipment.destination_warehouse.name,
            shipment.driver.name if shipment.driver else "",
            shipment.vehicle.registration_number if shipment.vehicle else "",
            shipment.get_status_display(),
            shipment.estimated_delivery_date,
        ])

    return response

