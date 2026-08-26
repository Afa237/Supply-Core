from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from inventory.models import StockMovement
from notifications.services import (
    create_alert,
    resolve_inventory_alert,
)

from .forms import (
    CustomerForm,
    CustomerTransactionForm,
)

from .models import (
    Customer,
    CustomerTransaction,
)

@login_required
def customer_list(request):

    customers = Customer.objects.annotate(
        transaction_count=Count(
            "transactions",
            distinct=True,
        )
    )

    query = request.GET.get(
        "q",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    )

    customer_type = request.GET.get(
        "type",
        "",
    )

    city = request.GET.get(
        "city",
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

    frequent = request.GET.get(
        "frequent",
        "",
    )


    # GENERAL SEARCH
    if query:

        customers = customers.filter(
            Q(name__icontains=query)
            | Q(contact_person__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
            | Q(city__icontains=query)
        )


    # STATUS
    if status:

        customers = customers.filter(
            status=status
        )


    # CUSTOMER TYPE
    if customer_type:

        customers = customers.filter(
            customer_type=customer_type
        )


    # CITY
    if city:

        customers = customers.filter(
            city__iexact=city
        )


    # CUSTOMER SINCE - FROM
    if date_from:

        customers = customers.filter(
            created_at__date__gte=date_from
        )


    # CUSTOMER SINCE - TO
    if date_to:

        customers = customers.filter(
            created_at__date__lte=date_to
        )


    # FREQUENT CUSTOMERS
    # For now: 5 or more transactions
    if frequent == "yes":

        customers = customers.filter(
            transaction_count__gte=5
        )


    cities = (
        Customer.objects
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
            "customers": customers,

            "query": query,

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


@login_required
def customer_detail(
    request,
    customer_id,
):

    customer = get_object_or_404(
        Customer,
        id=customer_id,
    )

    transactions = (
        customer.transactions
        .select_related(
            "inventory__product",
            "inventory__warehouse",
            "processed_by",
        )
        .all()
    )

    total_transactions = (
        transactions.count()
    )

    total_quantity_supplied = sum(
        transaction.quantity
        for transaction in transactions
    )

    last_transaction = (
        transactions.first()
    )

    return render(
        request,
        "customers/customer_detail.html",
        {
            "customer": customer,
            "transactions": transactions,
            "total_transactions":
                total_transactions,
            "total_quantity_supplied":
                total_quantity_supplied,
            "last_transaction":
                last_transaction,
        },
    )


@login_required
def customer_create(request):

    if request.method == "POST":

        form = CustomerForm(
            request.POST
        )

        if form.is_valid():

            customer = form.save()

            messages.success(
                request,
                "Customer created successfully.",
            )

            return redirect(
                "customer_detail",
                customer_id=customer.id,
            )

    else:

        form = CustomerForm()

    return render(
        request,
        "customers/customer_form.html",
        {
            "form": form,
            "page_title": "Add Customer",
        },
    )


@login_required
def customer_update(
    request,
    customer_id,
):

    customer = get_object_or_404(
        Customer,
        id=customer_id,
    )

    if request.method == "POST":

        form = CustomerForm(
            request.POST,
            instance=customer,
        )

        if form.is_valid():

            form.save()

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
            instance=customer
        )

    return render(
        request,
        "customers/customer_form.html",
        {
            "form": form,
            "page_title": "Edit Customer",
        },
    )
@login_required
@transaction.atomic
def customer_transaction_create(
    request,
    customer_id,
):

    customer = get_object_or_404(
        Customer,
        id=customer_id,
    )

    if request.method == "POST":

        form = CustomerTransactionForm(
            request.POST
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


            # Prevent stock from going below zero
            if quantity > inventory.quantity:

                form.add_error(
                    "quantity",
                    (
                        "This quantity exceeds "
                        "the available stock."
                    ),
                )

            else:

                # Deduct inventory
                inventory.quantity -= quantity

                inventory.save()


                # Save customer transaction
                customer_transaction.customer = (
                    customer
                )

                customer_transaction.processed_by = (
                    request.user
                )

                customer_transaction.save()


                # Record it inside existing stock history
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


                # Low-stock alert logic
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

        form = CustomerTransactionForm()


    return render(
        request,
        "customers/customer_transaction_form.html",
        {
            "customer": customer,
            "form": form,
        },
    )

# Create your views here.
