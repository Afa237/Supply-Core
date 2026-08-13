from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import (
    department_required,
    role_required,
)

from .forms import PurchaseOrderForm, PurchaseOrderItemForm
from .models import PurchaseOrder, PurchaseOrderItem


@login_required
@department_required("procurement")
@role_required("viewer")
def purchase_order_list(request):
    purchase_orders = PurchaseOrder.objects.select_related(
        "supplier"
    ).all()

    query = request.GET.get("q", "")
    status = request.GET.get("status", "")

    if query:
        purchase_orders = purchase_orders.filter(
            Q(po_number__icontains=query)
            | Q(supplier__name__icontains=query)
        )

    if status:
        purchase_orders = purchase_orders.filter(
            status=status
        )

    return render(
        request,
        "procurement/purchase_order_list.html",
        {
            "purchase_orders": purchase_orders,
            "query": query,
            "selected_status": status,
            "status_choices": PurchaseOrder.STATUS_CHOICES,
        },
    )


@login_required
@department_required("procurement")
@role_required("officer")
def purchase_order_create(request):
    if request.method == "POST":
        form = PurchaseOrderForm(request.POST)

        if form.is_valid():
            form.save()

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

    if request.method == "POST":
        form = PurchaseOrderForm(
            request.POST,
            instance=purchase_order,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Purchase order updated successfully.",
            )

            return redirect("purchase_order_list")
    else:
        form = PurchaseOrderForm(
            instance=purchase_order
        )

    return render(
        request,
        "procurement/purchase_order_form.html",
        {
            "form": form,
            "page_title": "Edit Purchase Order",
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
        purchase_order.delete()

        messages.success(
            request,
            "Purchase order deleted successfully.",
        )

        return redirect("purchase_order_list")

    return render(
        request,
        "procurement/purchase_order_confirm_delete.html",
        {
            "purchase_order": purchase_order,
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
