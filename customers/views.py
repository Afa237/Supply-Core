import csv
from django.contrib import messages 
from django.contrib.auth.decorators import login_required 
from django.db import transaction 
from django.db.models import Count, Q 
from django.http import HttpResponse 
from django.shortcuts import ( get_object_or_404, redirect, render, )
from accounts.access import filter_by_user_scope 
from accounts.decorators import role_required
from inventory.models import StockMovement
from notifications.services import ( create_alert, resolve_inventory_alert, )
from .forms import ( CustomerForm, CustomerTransactionForm, )
from .models import Customer


# =========================================================
# CUSTOMER LIST
# =========================================================
@login_required 
@role_required("viewer") 
def customer_list(request):
    customers = Customer.objects.select_related(
        "branch", "branch__company"
    ).annotate(transaction_count=Count("transactions", distinct=True))

    customers = filter_by_user_scope(customers, request.user)

# Keep an unfiltered-by-search copy for
# branch-secure filter choices.
    scoped_customers = customers

    query = request.GET.get("q", "").strip()

    status = request.GET.get("status", "")

    customer_type = request.GET.get("type", "")

    city = request.GET.get("city", "")

    date_from = request.GET.get("date_from", "")

    date_to = request.GET.get("date_to", "")

    frequent = request.GET.get("frequent", "")

    if query:
        customers = customers.filter(
            Q(name__icontains=query)
            | Q(
                contact_person__icontains=query
            )
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
            | Q(city__icontains=query)
            | Q(branch__name__icontains=query)
        )

    if status:
        customers = customers.filter(
            status=status
        )

    if customer_type:
        customers = customers.filter(
            customer_type=customer_type
        )

    if city:
        customers = customers.filter(
            city__iexact=city
        )

    if date_from:
        customers = customers.filter(
            created_at__date__gte=date_from
        )

    if date_to:
        customers = customers.filter(
            created_at__date__lte=date_to
        )

    if frequent == "yes":
        customers = customers.filter(
            transaction_count__gte=5
        )

    cities = (
    scoped_customers
    .exclude(city="")
    .values_list(
        "city",
        flat=True,
    )
    .distinct()
    .order_by("city")
)

    return render(
    request,
    "customers/customer_list.html",
    {
        "customers":
            customers,

        "query":
            query,

        "selected_status":
            status,

        "selected_type":
            customer_type,

        "selected_city":
            city,

        "selected_date_from":
            date_from,

        "selected_date_to":
            date_to,

        "selected_frequent":
            frequent,

        "status_choices":
            Customer.STATUS_CHOICES,

        "type_choices":
            Customer.CUSTOMER_TYPE_CHOICES,

        "cities":
            cities,
    },
)
# =========================================================
# CUSTOMER DETAIL
# =========================================================
@login_required 
@role_required("viewer") 
def customer_detail( request, customer_id, ):
    customers = (
        Customer.objects.select_related(
            "branch",
            "branch__company",
        )
    )

    customers = filter_by_user_scope(
        customers,
        request.user,
    )

    customer = get_object_or_404(
        customers,
        id=customer_id,
    )

    transactions = (
        customer.transactions
        .select_related(
            "inventory__product",
            "inventory__warehouse",
            "inventory__warehouse__branch",
            "processed_by",
        )
        .all()
    )

    total_transactions = (
        transactions.count()
    )

    total_quantity_supplied = sum(
        item.quantity
        for item in transactions
    )

    last_transaction = (
        transactions.first()
    )

    return render(
        request,"customers/customer_detail.html",
        {
            "customer":
                customer,

            "transactions":
                transactions,

            "total_transactions":
                total_transactions,

            "total_quantity_supplied":
                total_quantity_supplied,

            "last_transaction":
                last_transaction,
        },
    )
# =========================================================
# CREATE CUSTOMER
# =========================================================
@login_required 
@role_required("officer") 
def customer_create(request):
    if request.method == "POST":

        form = CustomerForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():

            customer = form.save(
                commit=False
            )

            profile = getattr(
                request.user,
                "profile",
                None,
            )

            # Branch employees always create customers
            # inside their own assigned branch.
            if (
                not request.user.is_superuser
                and profile
                and profile.role not in [
                    "admin",
                    "supply_chain_manager",
                ]
            ):

                customer.branch = (
                    profile.branch
                )

            if not customer.branch:

                form.add_error(
                    "branch",
                    "Please select a branch.",
                )

            else:

                customer.save()

                messages.success(
                    request,
                    (
                        "Customer created "
                        "successfully."
                    ),
                )

                return redirect(
                    "customer_detail",
                    customer_id=customer.id,
                )

    else:

        form = CustomerForm(
            user=request.user,
        )

    return render(
        request,
        "customers/customer_form.html",
        {
            "form":
                form,

            "page_title":
                "Add Customer",
        },
    )
# =========================================================
# UPDATE CUSTOMER
# =========================================================
@login_required 
@role_required("officer") 
def customer_update( request, customer_id, ):
    customers = (
        Customer.objects.select_related(
            "branch",
            "branch__company",
        )
    )

    customers = filter_by_user_scope(
        customers,
        request.user,
    )

    customer = get_object_or_404(
        customers,
        id=customer_id,
    )

    if request.method == "POST":

        form = CustomerForm(
            request.POST,
            instance=customer,
            user=request.user,
        )

        if form.is_valid():

            updated_customer = (
                form.save(commit=False)
            )

            profile = getattr(
                request.user,
                "profile",
                None,
            )

            if (
                not request.user.is_superuser
                and profile
                and profile.role not in [
                    "admin",
                    "supply_chain_manager",
                ]
            ):

                updated_customer.branch = (
                    profile.branch
                )

            updated_customer.save()

            messages.success(
                request,
                "Customer updated successfully.",
            )

            return redirect(
                "customer_detail",
                customer_id=customer.id,
            )

    else:

        form = CustomerForm(
            instance=customer,
            user=request.user,
        )

    return render(
        request,
        "customers/customer_form.html",
        {
            "form":
                form,

            "page_title":
                "Edit Customer",
        },
    )
# =========================================================
# RECORD CUSTOMER DISPATCH
# =========================================================
@login_required 
@role_required("officer") 
@transaction.atomic 
def customer_transaction_create( request, customer_id, ):
    customers = (
        Customer.objects.select_related(
            "branch",
            "branch__company",
        )
    )

    customers = filter_by_user_scope(
        customers,
        request.user,
    )

    customer = get_object_or_404(
        customers,
        id=customer_id,
    )

    if request.method == "POST":

        form = CustomerTransactionForm(
            request.POST,
            user=request.user,
            customer=customer,
        )

        if form.is_valid():

            customer_transaction = (
                form.save(commit=False)
            )

            inventory = (
                customer_transaction.inventory
            )

            quantity = (
                customer_transaction.quantity
            )

            # Extra protection:
            # customer and stock must belong
            # to the same branch.
            if (
                not customer.branch
                or inventory.warehouse.branch_id
                != customer.branch_id
            ):

                form.add_error(
                    "inventory",
                    (
                        "The selected inventory "
                        "does not belong to this "
                        "customer's branch."
                    ),
                )

            elif quantity > inventory.quantity:

                form.add_error(
                    "quantity",
                    (
                        "This quantity exceeds "
                        "the available stock."
                    ),
                )

            else:

                # Deduct inventory.
                inventory.quantity -= quantity
                inventory.save()

                # Save customer transaction.
                customer_transaction.customer = (
                    customer
                )

                customer_transaction.processed_by = (
                    request.user
                )

                customer_transaction.save()

                # Record the dispatch in
                # Inventory Stock Movement.
                StockMovement.objects.create(
                    inventory=inventory,
                    movement_type="stock_out",
                    quantity=quantity,
                    reference=(
                        customer_transaction.reference
                        or f"CUST-{customer.id}"
                    ),
                    notes=(
                        f"Dispatched to customer: "
                        f"{customer.name}. "
                        f"{customer_transaction.notes}"
                    ),
                    created_by=request.user,
                )

                # Low-stock alert.
                if (
                    inventory.quantity
                    <= inventory.product.reorder_level
                ):

                    create_alert(
                        alert_type="low_stock",
                        title=(
                            f"Low stock: "
                            f"{inventory.product.name}"
                        ),
                        message=(
                            f"{inventory.product.name} "
                            f"has fallen to "
                            f"{inventory.quantity} units "
                            f"at "
                            f"{inventory.warehouse.name}."
                        ),
                        severity="warning",
                        department="inventory",
                        source_model="Inventory",
                        source_object_id=inventory.id,
                        metadata={
                            "quantity":
                                inventory.quantity,

                            "reorder_level":
                                inventory.product.reorder_level,

                            "warehouse":
                                inventory.warehouse.name,

                            "branch": (
                                customer.branch.name
                                if customer.branch
                                else ""
                            ),
                        },
                    )

                else:

                    resolve_inventory_alert(
                        inventory
                    )

                messages.success(
                    request,
                    (
                        "Customer dispatch recorded "
                        "successfully."
                ),
            )

            return redirect(
                "customer_detail",
                customer_id=customer.id,
            )

    else:

        form = CustomerTransactionForm(
            user=request.user,
            customer=customer,
        )

    return render(
        request,
        "customers/customer_transaction_form.html",
        {
            "customer": customer,
            "form": form,
        },
    )
# =========================================================
# DOWNLOAD CUSTOMER HISTORY
# =========================================================
@login_required 
@role_required("viewer") 
def customer_history_csv( request, customer_id, ):
    customers = (
        Customer.objects.select_related(
            "branch",
            "branch__company",
        )
    )

    customers = filter_by_user_scope(
        customers,
        request.user,
    )

    customer = get_object_or_404(
        customers,
        id=customer_id,
    )

    transactions = (
        customer.transactions
        .select_related(
            "inventory__product",
            "inventory__warehouse",
            "inventory__warehouse__branch",
            "processed_by",
        )
        .order_by("-created_at")
    )

    response = HttpResponse(
        content_type="text/csv"
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; filename='
        f'"customer_{customer.id}_history.csv"'
    )

    writer = csv.writer(
        response
    )

    writer.writerow([
        "Customer",
        "Customer Type",
        "Branch",
        "Date",
        "Product",
        "SKU",
        "Warehouse",
        "Quantity",
        "Reference",
        "Processed By",
        "Notes",
    ])

    for item in transactions:

        processed_by = ""

        if item.processed_by:

            processed_by = (
                item.processed_by.get_full_name()
                or item.processed_by.username
            )

        writer.writerow([
            customer.name,
            customer.get_customer_type_display(),
            (
                customer.branch.name
                if customer.branch
                else ""
            ),
            item.created_at.strftime(
                "%Y-%m-%d %H:%M"
            ),
            item.inventory.product.name,
            item.inventory.product.sku,
            item.inventory.warehouse.name,
            item.quantity,
            item.reference,
            processed_by,
            item.notes,
        ])

    return response