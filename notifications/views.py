from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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

# Create your views here.
