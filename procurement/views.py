from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PurchaseOrderForm
from .models import PurchaseOrder


@login_required
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

# Create your views here.
