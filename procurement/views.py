from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import (
    department_required,
    role_required,
)
from django.db.models.deletion import ProtectedError
from .forms import PurchaseOrderForm, PurchaseOrderItemForm
from .models import PurchaseOrder, PurchaseOrderItem, Supplier
from audit.utils import log_action
from django.utils import timezone
from notifications.services import (
    create_alert,
    resolve_purchase_order_alert,
)

@login_required
@department_required("procurement")
@role_required("viewer")
def purchase_order_list(request):

    purchase_orders = PurchaseOrder.objects.select_related(
        "supplier"
    ).all()

    query = request.GET.get("q", "").strip()
    supplier_id = request.GET.get("supplier", "")
    status = request.GET.get("status", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    overdue = request.GET.get("overdue", "")


    if query:

        purchase_orders = purchase_orders.filter(
            Q(po_number__icontains=query)
            | Q(supplier__name__icontains=query)
        )


    if supplier_id:

        purchase_orders = purchase_orders.filter(
            supplier_id=supplier_id
        )


    if status:

        purchase_orders = purchase_orders.filter(
            status=status
        )


    if date_from:

        purchase_orders = purchase_orders.filter(
            expected_delivery__gte=date_from
        )


    if date_to:

        purchase_orders = purchase_orders.filter(
            expected_delivery__lte=date_to
        )


    if overdue == "yes":

        purchase_orders = purchase_orders.filter(
            expected_delivery__lt=timezone.localdate()
        ).exclude(
            status__in=[
                "received",
                "cancelled",
            ]
        )


    suppliers = Supplier.objects.all()


    return render(
        request,
        "procurement/purchase_order_list.html",
        {
            "purchase_orders": purchase_orders,
            "suppliers": suppliers,
            "query": query,
            "selected_supplier": supplier_id,
            "selected_status": status,
            "selected_date_from": date_from,
            "selected_date_to": date_to,
            "selected_overdue": overdue,
            "status_choices":
                PurchaseOrder.STATUS_CHOICES,
        },
    )


@login_required
@department_required("procurement")
@role_required("officer")
def purchase_order_create(request):
    if request.method == "POST":
        form = PurchaseOrderForm(request.POST)

        if form.is_valid():
            purchase_order = form.save()
            if purchase_order.status in ["received", "cancelled"]:
                resolve_purchase_order_alert(purchase_order)
            log_action(
                request,
                action="create",
                obj=purchase_order,
                description="Created purchase order.",
                )
            messages.success(
                request,
                "Purchase order created successfully.",
            )

            return redirect("purchase_order_list")
    else:
        form = PurchaseOrderForm()

    return render(
        request,
        "procurement/purchase_order_form.html",
        {
            "form": form,
            "page_title": "Create Purchase Order",
        },
    )


@login_required 
@department_required("procurement") 
@role_required("officer") 
def purchase_order_update(request, po_id):
    purchase_order = get_object_or_404(
        PurchaseOrder,
        id=po_id,
    )

    old_status = purchase_order.status

    if request.method == "POST":
        form = PurchaseOrderForm(
            request.POST,
            instance=purchase_order,
        )

        if form.is_valid():
            purchase_order = form.save()

            # Resolve overdue alert when PO is completed/cancelled
            if purchase_order.status in [
                "received",
                "cancelled",
            ]:
                resolve_purchase_order_alert(
                    purchase_order
                )

            # PROCUREMENT → LOGISTICS HANDOFF
            if (
                old_status
                not in ["approved", "ordered"]
                and purchase_order.status
                in ["approved", "ordered"]
            ):

                create_alert(
                alert_type="procurement_handoff",
                title=(
                    f"PO ready for Logistics: "
                    f"{purchase_order.po_number}"
                ),
                message=(
                    f"Purchase order "
                    f"{purchase_order.po_number} "
                    f"from "
                    f"{purchase_order.supplier.name} "
                    f"is now "
                    f"{purchase_order.get_status_display()} "
                    f"and requires Logistics action."
                ),
                severity="info",
                department="logistics",
                source_model="PurchaseOrder",
                source_object_id=purchase_order.id,
                metadata={
                    "po_number":
                        purchase_order.po_number,

                    "supplier":
                        purchase_order.supplier.name,

                    "status":
                        purchase_order.status,

                    "total_amount":
                        str(
                            purchase_order.total_amount
                        ),
                },
            )

                log_action(
                    request,
                action="status_change",
                obj=purchase_order,
                description=(
                    "Purchase order handed off "
                    "to Logistics."
                ),
                metadata={
                    "old_status": old_status,
                    "new_status":
                        purchase_order.status,
                },
            )

            else:

                log_action(
                    request,
                action="update",
                obj=purchase_order,
                description=(
                    "Updated purchase order."
                ),
                metadata={
                    "old_status": old_status,
                    "new_status":
                        purchase_order.status,
                },
            )

            messages.success(
                request,
                "Purchase order updated successfully.",
            )

            return redirect(
                "purchase_order_list"
            )

    else:

        form = PurchaseOrderForm(
            instance=purchase_order
        )

    return render(
        request,
        "procurement/purchase_order_form.html",
        {
            "form": form,
            "page_title":
                "Edit Purchase Order",
        },
    )


@login_required
@department_required("procurement")
@role_required("manager")
def purchase_order_delete(request, po_id):
    purchase_order = get_object_or_404(
        PurchaseOrder,
        id=po_id,
    )

    if request.method == "POST":

        log_action(
            request,
            action="delete",
            obj=purchase_order,
            description=(
                "Deleted purchase order."
            ),
        )

        try:
            purchase_order.delete()
        except ProtectedError:
            messages.error(
                request,
                (
                    "This Purchase Order cannot be deleted "
                    "because it already has a shipment "
                    "associated with it."
                ),
            )
            return redirect("purchase_order_list")

        messages.success(
            request,
            "Purchase order deleted successfully.",
        )

        return redirect(
            "purchase_order_list"
        )

    return render(
        request,
        "procurement/purchase_order_confirm_delete.html",
        {
            "purchase_order":
                purchase_order,
        },
    )


@login_required
@department_required("procurement")
@role_required("viewer")
def purchase_order_detail(request, po_id):
    purchase_order = get_object_or_404(
        PurchaseOrder.objects.select_related("supplier"),
        id=po_id,
    )

    return render(
        request,
        "procurement/purchase_order_detail.html",
        {
            "purchase_order": purchase_order,
        },
    )
@login_required
@department_required("procurement")
@role_required("officer")
def purchase_order_item_create(request, po_id):
    purchase_order = get_object_or_404(
        PurchaseOrder,
        id=po_id,
    )

    if request.method == "POST":
        form = PurchaseOrderItemForm(
            request.POST,
            supplier=purchase_order.supplier,
        )

        if form.is_valid():
            item = form.save(commit=False)
            item.purchase_order = purchase_order
            item.save()

            purchase_order.total_amount = (
                purchase_order.calculated_total
            )
            purchase_order.save(update_fields=["total_amount"])

            messages.success(
                request,
                "Purchase order item added successfully.",
            )

            return redirect(
                "purchase_order_detail",
                po_id=purchase_order.id,
            )
    else:
        form = PurchaseOrderItemForm(
            supplier=purchase_order.supplier
        )

    return render(
        request,
        "procurement/purchase_order_item_form.html",
        {
            "form": form,
            "purchase_order": purchase_order,
            "page_title": "Add Purchase Order Item",
        },
    )


@login_required
@department_required("procurement")
@role_required("officer")
def purchase_order_item_update(request, item_id):
    item = get_object_or_404(
        PurchaseOrderItem.objects.select_related(
            "purchase_order",
            "purchase_order__supplier",
        ),
        id=item_id,
    )

    if request.method == "POST":
        form = PurchaseOrderItemForm(
            request.POST,
            instance=item,
            supplier=item.purchase_order.supplier,
        )

        if form.is_valid():
            form.save()

            item.purchase_order.total_amount = (
                item.purchase_order.calculated_total
            )
            item.purchase_order.save(
                update_fields=["total_amount"]
            )

            messages.success(
                request,
                "Purchase order item updated successfully.",
            )

            return redirect(
                "purchase_order_detail",
                po_id=item.purchase_order.id,
            )
    else:
        form = PurchaseOrderItemForm(
            instance=item,
            supplier=item.purchase_order.supplier,
        )

    return render(
        request,
        "procurement/purchase_order_item_form.html",
        {
            "form": form,
            "purchase_order": item.purchase_order,
            "page_title": "Edit Purchase Order Item",
        },
    )


@login_required
@department_required("procurement")
@role_required("officer")
def purchase_order_item_delete(request, item_id):
    item = get_object_or_404(
        PurchaseOrderItem.objects.select_related(
            "purchase_order"
        ),
        id=item_id,
    )

    purchase_order = item.purchase_order

    if request.method == "POST":
        item.delete()

        purchase_order.total_amount = (
            purchase_order.calculated_total
        )
        purchase_order.save(update_fields=["total_amount"])

        messages.success(
            request,
            "Purchase order item deleted successfully.",
        )

        return redirect(
            "purchase_order_detail",
            po_id=purchase_order.id,
        )

    return render(
        request,
        "procurement/purchase_order_item_confirm_delete.html",
        {
            "item": item,
            "purchase_order": purchase_order,
        },
    )

# Create your views here.
