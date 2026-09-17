from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from accounts.models import Company, Branch
from suppliers.models import Supplier
from products.models import Category, Product
from procurement.models import PurchaseOrder, PurchaseOrderItem
from warehouse.models import Warehouse
from inventory.models import Inventory, StockMovement
from logistics.models import Driver, Vehicle, Shipment
from customers.models import Customer, CustomerTransaction

TODAY = timezone.localdate()


def money(value):
    return Decimal(str(value))


def get_user(username):
    return get_user_model().objects.filter(username=username).first()


def find_branch(company, country_word):
    branch = Branch.objects.filter(company=company, country__icontains=country_word).first()
    if not branch:
        branch = Branch.objects.filter(company=company, name__icontains=country_word).first()
    if not branch:
        raise RuntimeError(f"Could not find the {country_word} branch for {company.name}.")
    return branch


def create_po(number, branch, supplier, status, order_offset, delivery_offset, lines, remarks):
    po = PurchaseOrder.objects.create(
        po_number=number,
        supplier=supplier,
        branch=branch,
        order_date=TODAY + timedelta(days=order_offset),
        expected_delivery=TODAY + timedelta(days=delivery_offset),
        status=status,
        remarks=remarks,
        total_amount=0,
    )
    total = Decimal("0.00")
    for product, qty in lines:
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            product=product,
            quantity=qty,
            unit_price=product.unit_price,
        )
        total += product.unit_price * qty
    po.total_amount = total
    po.save(update_fields=["total_amount"])
    return po


@transaction.atomic
def seed():
    company = Company.objects.filter(name__iexact="Supply Core Demo Company").first()
    if not company:
        company = Company.objects.first()
    if not company:
        raise RuntimeError("No Company exists. Create Supply Core Demo Company first.")

    cmr = find_branch(company, "Cameroon")
    nga = find_branch(company, "Nigeria")

    florence = get_user("Florence")
    scm_manager = get_user("Flor@")
    emma = get_user("Emma")
    lucia = get_user("Lucia")

    print("Resetting operational demo data...")

    CustomerTransaction.objects.all().delete()
    StockMovement.objects.all().delete()
    Shipment.objects.all().delete()
    Driver.objects.all().delete()
    Vehicle.objects.all().delete()
    Inventory.objects.all().delete()
    PurchaseOrderItem.objects.all().delete()
    PurchaseOrder.objects.all().delete()
    Customer.objects.all().delete()
    Warehouse.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Supplier.objects.all().delete()

    # Old alerts point to old operational objects, so clear them if the model exists.
    try:
        from notifications.models import Alert
        Alert.objects.all().delete()
    except Exception:
        pass

    # ---------- SUPPLIERS ----------
    suppliers = {}
    supplier_rows = [
        ("Central Africa Office Supplies", "Marie Nfor", "Douala", "Cameroon", 5),
        ("Gulf Industrial Materials", "Daniel Ewane", "Douala", "Cameroon", 4),
        ("Lagos Business Systems", "Chinedu Okafor", "Lagos", "Nigeria", 5),
        ("West Africa Building Materials", "Amina Bello", "Abuja", "Nigeria", 4),
        ("Regional Safety & Packaging", "Grace Mensah", "Accra", "Ghana", 4),
    ]
    for i, (name, contact, city, country, rating) in enumerate(supplier_rows, start=1):
        suppliers[name] = Supplier.objects.create(
            name=name,
            contact_person=contact,
            email=f"supplier{i}@supplycore.demo",
            phone=f"+2376000000{i}" if country == "Cameroon" else f"+2348000000{i}",
            address=f"Commercial District, {city}",
            city=city,
            country=country,
            status="active",
            rating=rating,
            notes="Approved demonstration supplier.",
        )

    # ---------- CATEGORIES ----------
    office = Category.objects.create(name="Office & IT", description="Office consumables, furniture and IT equipment")
    construction = Category.objects.create(name="Construction Materials", description="Materials used for construction and infrastructure")
    safety = Category.objects.create(name="Safety & Packaging", description="PPE and warehouse packaging materials")

    # ---------- PRODUCTS ----------
    product_rows = [
        ("A4 Printing Paper (500 Sheets)", "SC-PAP-001", office, "Central Africa Office Supplies", "box", "6500.00", 50),
        ("Executive Office Chair", "SC-FUR-002", office, "Central Africa Office Supplies", "pcs", "85000.00", 10),
        ("HP ProBook 450 G10 Laptop", "SC-IT-003", office, "Lagos Business Systems", "pcs", "625000.00", 5),
        ("Portland Cement 50kg", "SC-CON-004", construction, "West Africa Building Materials", "bag", "7500.00", 80),
        ("12mm Reinforcement Steel Bar", "SC-CON-005", construction, "Gulf Industrial Materials", "pcs", "9500.00", 40),
        ("Industrial Safety Helmet", "SC-SAF-006", safety, "Regional Safety & Packaging", "pcs", "12000.00", 25),
        ("Wireless Barcode Scanner", "SC-IT-007", office, "Lagos Business Systems", "pcs", "78000.00", 8),
        ("Industrial Pallet Wrap", "SC-PKG-008", safety, "Regional Safety & Packaging", "roll", "18000.00", 20),
    ]

    # 'roll' is not in current UNIT_CHOICES, so use pcs for pallet wrap to stay within the model choices.
    products = {}
    for name, sku, category, supplier_name, unit, price, reorder in product_rows:
        if unit == "roll":
            unit = "pcs"
        products[sku] = Product.objects.create(
            name=name,
            sku=sku,
            category=category,
            supplier=suppliers[supplier_name],
            unit=unit,
            unit_price=money(price),
            reorder_level=reorder,
            description="Demo catalogue item used for branch-aware supply-chain operations.",
        )

    # ---------- WAREHOUSES ----------
    cmr_wh = Warehouse.objects.create(
        name="Buea Central Warehouse",
        code="CMR-BUE-01",
        manager_name="Cameroon Warehouse Lead",
        phone="+237670000001",
        email="buea.warehouse@supplycore.demo",
        address="Molyko Industrial Zone",
        city="Buea",
        country="Cameroon",
        capacity=5000,
        status="active",
        notes="Primary Cameroon branch distribution warehouse.",
        branch=cmr,
    )
    nga_wh = Warehouse.objects.create(
        name="Lagos Distribution Hub",
        code="NGA-LAG-01",
        manager_name="Nigeria Warehouse Lead",
        phone="+234810000001",
        email="lagos.warehouse@supplycore.demo",
        address="Ikeja Industrial Estate",
        city="Lagos",
        country="Nigeria",
        capacity=6500,
        status="active",
        notes="Primary Nigeria branch distribution warehouse.",
        branch=nga,
    )

    # ---------- INVENTORY ----------
    cmr_stock = {
        "SC-PAP-001": 180,
        "SC-FUR-002": 8,     # low stock
        "SC-IT-003": 14,
        "SC-CON-004": 220,
        "SC-CON-005": 35,    # low stock
        "SC-SAF-006": 75,
        "SC-IT-007": 16,
        "SC-PKG-008": 45,
    }
    nga_stock = {
        "SC-PAP-001": 120,
        "SC-FUR-002": 18,
        "SC-IT-003": 4,      # low stock
        "SC-CON-004": 95,
        "SC-CON-005": 60,
        "SC-SAF-006": 20,    # low stock
        "SC-IT-007": 11,
        "SC-PKG-008": 55,
    }

    # Planned customer dispatch quantities are included in opening stock so
    # stock-in minus dispatches reconciles exactly to the final quantity shown.
    planned_dispatch_totals = {
        ("CMR", "SC-IT-003"): 2,
        ("CMR", "SC-PAP-001"): 10,
        ("CMR", "SC-FUR-002"): 2,
        ("CMR", "SC-CON-004"): 20,
        ("NGA", "SC-PAP-001"): 12,
        ("NGA", "SC-CON-005"): 15,
        ("NGA", "SC-PKG-008"): 10,
        ("NGA", "SC-SAF-006"): 5,
    }

    inventory = {}
    for branch_code, warehouse, stock, user in [
        ("CMR", cmr_wh, cmr_stock, emma or florence),
        ("NGA", nga_wh, nga_stock, lucia or florence),
    ]:
        for sku, final_qty in stock.items():
            inv = Inventory.objects.create(product=products[sku], warehouse=warehouse, quantity=final_qty)
            inventory[(branch_code, sku)] = inv
            opening_qty = final_qty + planned_dispatch_totals.get((branch_code, sku), 0)
            StockMovement.objects.create(
                inventory=inv,
                movement_type="stock_in",
                quantity=opening_qty,
                reference=f"OPEN-{branch_code}-{sku}",
                notes="Opening stock for demonstration dataset.",
                created_by=user,
            )

    # ---------- PURCHASE ORDERS ----------
    cmr_po1 = create_po(
        "PO-CMR-260901", cmr, suppliers["Central Africa Office Supplies"], "received", -16, -8,
        [(products["SC-PAP-001"], 100), (products["SC-FUR-002"], 20)],
        "Completed office replenishment for Cameroon branch.",
    )
    cmr_po2 = create_po(
        "PO-CMR-260912", cmr, suppliers["Gulf Industrial Materials"], "ordered", -5, 4,
        [(products["SC-CON-005"], 100), (products["SC-SAF-006"], 60)],
        "Active replenishment for steel and PPE.",
    )
    cmr_po3 = create_po(
        "PO-CMR-260917", cmr, suppliers["Lagos Business Systems"], "pending", 0, 10,
        [(products["SC-IT-007"], 15)],
        "Awaiting approval for barcode scanning equipment.",
    )

    nga_po1 = create_po(
        "PO-NGA-260902", nga, suppliers["Lagos Business Systems"], "received", -15, -7,
        [(products["SC-IT-003"], 10), (products["SC-IT-007"], 12)],
        "Completed IT replenishment for Nigeria branch.",
    )
    nga_po2 = create_po(
        "PO-NGA-260911", nga, suppliers["West Africa Building Materials"], "approved", -6, 3,
        [(products["SC-CON-004"], 180), (products["SC-CON-005"], 120)],
        "Approved construction-material replenishment.",
    )
    nga_po3 = create_po(
        "PO-NGA-260916", nga, suppliers["Regional Safety & Packaging"], "ordered", -1, 6,
        [(products["SC-SAF-006"], 80), (products["SC-PKG-008"], 70)],
        "Urgent safety and packaging replenishment.",
    )

    # ---------- DRIVERS & VEHICLES ----------
    cmr_driver = Driver.objects.create(name="Daniel Mbarga", phone="+237671111111", licence_number="CMR-DL-001", active=True, branch=cmr)
    cmr_driver2 = Driver.objects.create(name="Brenda Nfor", phone="+237672222222", licence_number="CMR-DL-002", active=True, branch=cmr)
    nga_driver = Driver.objects.create(name="Tunde Adeyemi", phone="+234811111111", licence_number="NGA-DL-001", active=True, branch=nga)
    nga_driver2 = Driver.objects.create(name="Ada Okeke", phone="+234822222222", licence_number="NGA-DL-002", active=True, branch=nga)

    cmr_truck = Vehicle.objects.create(registration_number="SW-451-AB", vehicle_type="truck", capacity=3000, active=True, branch=cmr)
    cmr_van = Vehicle.objects.create(registration_number="SW-882-CD", vehicle_type="van", capacity=1200, active=True, branch=cmr)
    nga_truck = Vehicle.objects.create(registration_number="LAG-452-XP", vehicle_type="truck", capacity=3500, active=True, branch=nga)
    nga_van = Vehicle.objects.create(registration_number="LAG-901-QT", vehicle_type="van", capacity=1500, active=True, branch=nga)

    # ---------- SHIPMENTS ----------
    Shipment.objects.create(
        tracking_number="SHP-CMR-260901",
        purchase_order=cmr_po1,
        destination_warehouse=cmr_wh,
        driver=cmr_driver,
        vehicle=cmr_truck,
        status="delivered",
        inventory_received=True,
        dispatch_date=TODAY - timedelta(days=13),
        estimated_delivery_date=TODAY - timedelta(days=9),
        actual_delivery_date=TODAY - timedelta(days=9),
        origin="Douala, Cameroon",
        notes="Delivered and received into Cameroon inventory.",
        created_by=emma or florence,
        branch=cmr,
    )
    Shipment.objects.create(
        tracking_number="SHP-CMR-260912",
        purchase_order=cmr_po2,
        destination_warehouse=cmr_wh,
        driver=cmr_driver2,
        vehicle=cmr_van,
        status="in_transit",
        inventory_received=False,
        dispatch_date=TODAY - timedelta(days=2),
        estimated_delivery_date=TODAY + timedelta(days=2),
        origin="Douala Port, Cameroon",
        notes="In transit to Buea Central Warehouse.",
        created_by=emma or florence,
        branch=cmr,
    )
    Shipment.objects.create(
        tracking_number="SHP-NGA-260902",
        purchase_order=nga_po1,
        destination_warehouse=nga_wh,
        driver=nga_driver,
        vehicle=nga_van,
        status="delivered",
        inventory_received=True,
        dispatch_date=TODAY - timedelta(days=12),
        estimated_delivery_date=TODAY - timedelta(days=8),
        actual_delivery_date=TODAY - timedelta(days=8),
        origin="Lagos Mainland, Nigeria",
        notes="Delivered and received into Nigeria inventory.",
        created_by=lucia or florence,
        branch=nga,
    )
    Shipment.objects.create(
        tracking_number="SHP-NGA-260916",
        purchase_order=nga_po3,
        destination_warehouse=nga_wh,
        driver=nga_driver2,
        vehicle=nga_truck,
        status="delayed",
        inventory_received=False,
        dispatch_date=TODAY - timedelta(days=1),
        estimated_delivery_date=TODAY + timedelta(days=2),
        origin="Apapa, Lagos, Nigeria",
        notes="Delay recorded for demonstration of exception monitoring.",
        created_by=lucia or florence,
        branch=nga,
    )

    # ---------- CUSTOMERS ----------
    customer_rows = [
        (cmr, "Buea Tech Solutions", "business", "Molyko", "Buea", "Cameroon", "contact@bueatech.demo"),
        (cmr, "Mount Cameroon Retail", "retailer", "Great Soppo", "Buea", "Cameroon", "orders@mcr.demo"),
        (cmr, "Fako Construction Services", "wholesaler", "Mile 17", "Buea", "Cameroon", "procurement@fako.demo"),
        (nga, "Ikeja Office Mart", "retailer", "Ikeja", "Lagos", "Nigeria", "orders@ikejamart.demo"),
        (nga, "Lagos BuildPro Ltd", "business", "Surulere", "Lagos", "Nigeria", "procurement@buildpro.demo"),
        (nga, "WestLink Distribution", "distributor", "Yaba", "Lagos", "Nigeria", "sales@westlink.demo"),
    ]
    customers = {}
    for i, (branch, name, ctype, address, city, country, email) in enumerate(customer_rows, start=1):
        customers[name] = Customer.objects.create(
            branch=branch,
            name=name,
            customer_type=ctype,
            contact_person=f"Demo Contact {i}",
            phone=f"+2376900000{i}" if country == "Cameroon" else f"+2348900000{i}",
            email=email,
            address=address,
            city=city,
            country=country,
            status="active",
            notes="Active demonstration customer.",
        )

    # ---------- CUSTOMER DISPATCH HISTORY ----------
    dispatches = [
        ("Buea Tech Solutions", "CMR", "SC-IT-003", 2, "DSP-CMR-001", emma or florence),
        ("Buea Tech Solutions", "CMR", "SC-PAP-001", 10, "DSP-CMR-002", emma or florence),
        ("Mount Cameroon Retail", "CMR", "SC-FUR-002", 2, "DSP-CMR-003", emma or florence),
        ("Fako Construction Services", "CMR", "SC-CON-004", 20, "DSP-CMR-004", emma or florence),
        ("Ikeja Office Mart", "NGA", "SC-PAP-001", 12, "DSP-NGA-001", lucia or florence),
        ("Lagos BuildPro Ltd", "NGA", "SC-CON-005", 15, "DSP-NGA-002", lucia or florence),
        ("WestLink Distribution", "NGA", "SC-PKG-008", 10, "DSP-NGA-003", lucia or florence),
        ("WestLink Distribution", "NGA", "SC-SAF-006", 5, "DSP-NGA-004", lucia or florence),
    ]
    for customer_name, branch_code, sku, qty, ref, user in dispatches:
        inv = inventory[(branch_code, sku)]
        CustomerTransaction.objects.create(
            customer=customers[customer_name],
            inventory=inv,
            quantity=qty,
            reference=ref,
            notes="Completed customer dispatch for demo history.",
            processed_by=user,
        )
        StockMovement.objects.create(
            inventory=inv,
            movement_type="stock_out",
            quantity=qty,
            reference=ref,
            notes=f"Customer dispatch to {customer_name}.",
            created_by=user,
        )

    print("\nDEMO DATA READY")
    print("Company:", company.name)
    print("Branches:", cmr.name, "|", nga.name)
    print("Suppliers:", Supplier.objects.count())
    print("Products:", Product.objects.count())
    print("Warehouses:", Warehouse.objects.count())
    print("Inventory records:", Inventory.objects.count())
    print("Purchase orders:", PurchaseOrder.objects.count())
    print("Shipments:", Shipment.objects.count())
    print("Customers:", Customer.objects.count())
    print("Customer transactions:", CustomerTransaction.objects.count())
    print("Stock movements:", StockMovement.objects.count())


seed()
