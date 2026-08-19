from .models import AuditLog


def get_client_ip(request):

    forwarded = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.META.get(
        "REMOTE_ADDR"
    )


def log_action(
    request,
    action,
    obj=None,
    model_name=None,
    description="",
    metadata=None,
):

    user = (
        request.user
        if request.user.is_authenticated
        else None
    )

    profile = (
        getattr(user, "profile", None)
        if user
        else None
    )

    department = (
        profile.department
        if profile
        else ""
    )

    if obj is not None:
        model_name = (
            model_name
            or obj.__class__.__name__
        )

        object_id = str(
            getattr(obj, "pk", "")
        )

        object_repr = str(obj)

    else:
        object_id = ""
        object_repr = ""

    AuditLog.objects.create(
        user=user,
        department=department,
        action=action,
        model_name=model_name or "Unknown",
        object_id=object_id,
        object_repr=object_repr,
        description=description,
        metadata=metadata or {},
        ip_address=get_client_ip(request),
    )