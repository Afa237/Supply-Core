from django.utils import timezone

from .models import Alert


def create_alert(
    *,
    alert_type,
    title,
    message,
    severity="warning",
    department="",
    source_model="",
    source_object_id="",
    metadata=None,
):

    alert, created = Alert.objects.get_or_create(
        alert_type=alert_type,
        source_model=source_model,
        source_object_id=str(source_object_id),
        status="open",
        defaults={
            "title": title,
            "message": message,
            "severity": severity,
            "department": department,
            "metadata": metadata or {},
        },
    )

    return alert


def resolve_alert(alert):

    alert.status = "resolved"
    alert.resolved_at = timezone.now()

    alert.save(
        update_fields=[
            "status",
            "resolved_at",
        ]
    )

def resolve_source_alerts(
    *,
    alert_type,
    source_model,
    source_object_id,
):
    alerts = Alert.objects.filter(
        alert_type=alert_type,
        source_model=source_model,
        source_object_id=str(source_object_id),
    ).exclude(
        status="resolved"
    )

    alerts.update(
        status="resolved",
        resolved_at=timezone.now(),
    )


def resolve_inventory_alert(inventory):

    resolve_source_alerts(
        alert_type="low_stock",
        source_model="Inventory",
        source_object_id=inventory.id,
    )


def resolve_shipment_alert(shipment):

    resolve_source_alerts(
        alert_type="shipment_delay",
        source_model="Shipment",
        source_object_id=shipment.id,
    )


def resolve_purchase_order_alert(purchase_order):

    resolve_source_alerts(
        alert_type="overdue_po",
        source_model="PurchaseOrder",
        source_object_id=purchase_order.id,
    )