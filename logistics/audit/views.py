from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.decorators import role_required

from .models import AuditLog


@login_required
@role_required("supply_chain_manager")
def audit_log_list(request):

    logs = AuditLog.objects.select_related(
        "user"
    ).all()[:500]

    return render(
        request,
        "audit/audit_log_list.html",
        {
            "logs": logs,
        },
    )

# Create your views here.
