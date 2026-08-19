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