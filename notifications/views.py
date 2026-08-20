from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from .models import Alert


@login_required
def alert_list(request):

    user = request.user
    profile = getattr(user, "profile", None)

    if (
        user.is_superuser
        or (
            profile
            and profile.role in [
                "admin",
                "supply_chain_manager",
            ]
        )
    ):
        alerts = Alert.objects.all()

    elif profile:
        alerts = Alert.objects.filter(
            department=profile.department
        )

    else:
        alerts = Alert.objects.none()

    return render(
        request,
        "notifications/alert_list.html",
        {
            "alerts": alerts,
        },
    )
@login_required
def acknowledge_alert(request, alert_id):

    alert = get_object_or_404(
        Alert,
        id=alert_id,
    )

    if request.method != "POST":
        return redirect("alert_list")

    alert.status = "resolved"

    alert.save(
        update_fields=[
            "status",
        ]
    )

    messages.success(
        request,
        "Alert acknowledged.",
    )

    return redirect(
        "alert_list"
    )
@login_required
def resolve_alert_view(request, alert_id):

    alert = get_object_or_404(
        Alert,
        id=alert_id,
    )

    if request.method != "POST":
        return redirect("alert_list")

    alert.status = "resolved"
    alert.resolved_at = timezone.now()

    alert.save(
        update_fields=[
            "status",
            "resolved_at",
        ]
    )

    messages.success(
        request,
        "Alert resolved successfully.",
    )

    return redirect(
        "alert_list"
    )
# Create your views here.
