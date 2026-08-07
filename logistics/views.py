from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DriverForm, ShipmentForm, VehicleForm
from .models import Driver, Shipment, Vehicle
from inventory.models import Inventory,StockMovement


@login_required
def shipment_list(request):
    shipments = Shipment.objects.select_related(
        "purchase_order",
        "destination_warehouse",
        "driver",
        "vehicle",
    )

    query = request.GET.get("q", "")
    status = request.GET.get("status", "")

    if query:
        shipments = shipments.filter(
            Q(tracking_number__icontains=query)
            | Q(purchase_order__po_number__icontains=query)
            | Q(origin__icontains=query)
            | Q(destination_warehouse__name__icontains=query)
        )

    if status:
        shipments = shipments.filter(status=status)

    return render(
        request,
        "logistics/shipment_list.html",
        {
            "shipments": shipments,
            "query": query,
            "selected_status": status,
            "status_choices": Shipment.STATUS_CHOICES,
        },
    )


@login_required
def shipment_create(request):
    if request.method == "POST":
        form = ShipmentForm(request.POST)

        if form.is_valid():
            shipment = form.save(commit=False)
            shipment.created_by = request.user
            shipment.save()

            messages.success(
                request,
                "Shipment created successfully.",
            )

            return redirect("shipment_list")
    else:
        form = ShipmentForm()

    return render(
        request,
        "logistics/shipment_form.html",
        {
            "form": form,
            "page_title": "Create Shipment",
        },
    )


@login_required
def shipment_update(request, shipment_id):
    shipment = get_object_or_404(
        Shipment,
        id=shipment_id,
    )

    if request.method == "POST":
        form = ShipmentForm(
            request.POST,
            instance=shipment,
        )

        if form.is_valid():
            form.save()

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
def shipment_detail(request, shipment_id):
    shipment = get_object_or_404(
        Shipment.objects.select_related(
            "purchase_order",
            "destination_warehouse",
            "driver",
            "vehicle",
            "created_by",
        ),
        id=shipment_id,
    )

    return render(
        request,
        "logistics/shipment_detail.html",
        {"shipment": shipment},
    )


@login_required
def shipment_delete(request, shipment_id):
    shipment = get_object_or_404(
        Shipment,
        id=shipment_id,
    )

    if request.method == "POST":
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
def driver_list(request):
    drivers = Driver.objects.all()

    return render(
        request,
        "logistics/driver_list.html",
        {"drivers": drivers},
    )


@login_required
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
def vehicle_list(request):
    vehicles = Vehicle.objects.all()

    return render(
        request,
        "logistics/vehicle_list.html",
        {"vehicles": vehicles},
    )


@login_required
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