from .models import Alert


def alert_count(request):

    if not request.user.is_authenticated:
        return {
            "active_alert_count": 0
        }

    profile = getattr(
        request.user,
        "profile",
        None,
    )

    if (
        request.user.is_superuser
        or (
            profile
            and profile.role in [
                "admin",
                "supply_chain_manager",
            ]
        )
    ):
        count = Alert.objects.filter(
            status="open"
        ).count()

    elif profile:
        count = Alert.objects.filter(
            status="open",
            department=profile.department,
        ).count()

    else:
        count = 0

    return {
        "active_alert_count": count
    }