from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from accounts.decorators import role_required

from .models import AuditLog


User = get_user_model()


@login_required
@role_required("supply_chain_manager")
def audit_log_list(request):

    logs = AuditLog.objects.select_related(
        "user"
    ).all()

    query = request.GET.get(
        "q",
        "",
    ).strip()

    user_id = request.GET.get(
        "user",
        "",
    )

    department = request.GET.get(
        "department",
        "",
    )

    action = request.GET.get(
        "action",
        "",
    )

    model_name = request.GET.get(
        "model",
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


    # GENERAL SEARCH
    if query:

        logs = logs.filter(
            Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(description__icontains=query)
            | Q(object_repr__icontains=query)
            | Q(model_name__icontains=query)
        )


    # USER
    if user_id:

        logs = logs.filter(
            user_id=user_id
        )


    # DEPARTMENT
    if department:

        logs = logs.filter(
            department=department
        )


    # ACTION
    if action:

        logs = logs.filter(
            action=action
        )


    # MODULE / MODEL
    if model_name:

        logs = logs.filter(
            model_name=model_name
        )


    # DATE FROM
    if date_from:

        logs = logs.filter(
            created_at__date__gte=date_from
        )


    # DATE TO
    if date_to:

        logs = logs.filter(
            created_at__date__lte=date_to
        )


    # Filter options
    users = User.objects.filter(
        audit_logs__isnull=False
    ).distinct().order_by("username")


    departments = (
        AuditLog.objects
        .exclude(department="")
        .values_list(
            "department",
            flat=True,
        )
        .distinct()
        .order_by("department")
    )


    model_names = (
        AuditLog.objects
        .exclude(model_name="")
        .values_list(
            "model_name",
            flat=True,
        )
        .distinct()
        .order_by("model_name")
    )


    logs = logs[:500]


    return render(
        request,
        "audit/audit_log_list.html",
        {
            "logs": logs,

            "users": users,
            "departments": departments,
            "action_choices":
                AuditLog.ACTION_CHOICES,
            "model_names": model_names,

            "query": query,
            "selected_user": user_id,
            "selected_department": department,
            "selected_action": action,
            "selected_model": model_name,
            "selected_date_from": date_from,
            "selected_date_to": date_to,
        },
    )