from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, ProductForm
from .models import Category, Product


@login_required
def product_list(request):
    products = Product.objects.select_related("category", "supplier").all()
    categories = Category.objects.all()

    query = request.GET.get("q", "")
    category_id = request.GET.get("category", "")

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(supplier__name__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
            "selected_category": category_id,
        },
    )


@login_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("product_list")
    else:
        form = ProductForm()

    return render(
        request,
        "products/product_form.html",
        {
            "form": form,
            "page_title": "Add Product",
        },
    )


@login_required
def product_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)

        if form.is_valid():
            form.save()
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "products/product_form.html",
        {
            "form": form,
            "page_title": "Edit Product",
        },
    )


@login_required
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.delete()
        return redirect("product_list")

    return render(
        request,
        "products/product_confirm_delete.html",
        {"product": product},
    )


@login_required
def category_list(request):
    categories = Category.objects.all()

    return render(
        request,
        "products/category_list.html",
        {"categories": categories},
    )


@login_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("category_list")
    else:
        form = CategoryForm()

    return render(
        request,
        "products/category_form.html",
        {
            "form": form,
            "page_title": "Add Category",
        },
    )

# Create your views here.
