from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import UserProfile
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .forms import StaffCreateForm
from .services import send_staff_invitation
from audit.utils import log_action
User = get_user_model()


def admin_access_required(view_func):
    def wrapper(request, *args, **kwargs):

        user = request.user
        profile = getattr(user, "profile", None)

        allowed = (
            user.is_superuser
            or (
                profile
                and profile.role in [
                    "admin",
                    "supply_chain_manager",
                ]
            )
        )

        if not allowed:
            messages.error(
                request,
                "You do not have permission to manage users.",
            )
            return redirect("home")

        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
@admin_access_required
def user_list(request):

    users = User.objects.select_related(
        "profile"
    ).order_by("username")

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": users,
        },
    )
@login_required
@admin_access_required
@transaction.atomic
def user_create(request):

    if request.method == "POST":

        form = StaffCreateForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            # Staff member must create their own password.
            user.set_unusable_password()

            user.is_active = True

            user.save()


            profile, created = UserProfile.objects.get_or_create(
                user=user
            )

            profile.department = (
                form.cleaned_data["department"]
            )

            profile.role = (
                form.cleaned_data["role"]
            )

            profile.save()


            # Generate secure password setup token
            send_staff_invitation(
                request,
                user,
                )

            messages.success(
                request,
                (
                    f"Account for {user.username} "
                    "created successfully. "
                    "Password setup instructions were sent."
                ),
            )

            return redirect(
                "user_list"
            )

    else:

        form = StaffCreateForm()


    return render(
        request,
        "accounts/user_create.html",
        {
            "form": form,
        },
    )

@login_required
@admin_access_required
def user_update(request, user_id):

    user = get_object_or_404(
        User,
        id=user_id,
    )

    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    if request.method == "POST":
        
        old_department = profile.department
        old_role = profile.role
        old_active = user.is_active

        user.first_name = request.POST.get(
            "first_name",
            "",
        ).strip()

        user.last_name = request.POST.get(
            "last_name",
            "",
        ).strip()

        user.email = request.POST.get(
            "email",
            "",
        ).strip()

        user.is_active = (
            request.POST.get("is_active") == "on"
        )

        profile.department = request.POST.get(
            "department",
            "",
        )

        profile.role = request.POST.get(
            "role",
            "viewer",
        )

        user.save()
        profile.save()

        log_action(
            request,
            action="permission_change",
            obj=user,
            model_name="User",
            description="Updated staff account access.",
            metadata={
                "old_department": old_department,
                "new_department": profile.department,
                "old_role": old_role,
                "new_role": profile.role,
                "old_active": old_active,
                "new_active": user.is_active,
            }
        )
        messages.success(
            request,
            "User account updated successfully.",
        )

        return redirect("user_list")

    return render(
        request,
        "accounts/user_update.html",
        {
            "managed_user": user,
            "profile": profile,
            "department_choices":
                UserProfile.DEPARTMENT_CHOICES,
            "role_choices":
                UserProfile.ROLE_CHOICES,
        },
    )
@login_required
@admin_access_required
def resend_invitation(request, user_id):

    user = get_object_or_404(
        User.objects.select_related("profile"),
        id=user_id,
    )

    if request.method != "POST":
        return redirect("user_list")

    if not user.email:
        messages.error(
            request,
            "This user does not have an email address.",
        )

        return redirect("user_list")

    if user.has_usable_password():
        messages.warning(
            request,
            (
                "This user has already created a password. "
                "Use password reset instead."
            ),
        )

        return redirect("user_list")

    send_staff_invitation(
        request,
        user,
    )

    messages.success(
        request,
        f"Invitation resent to {user.email}.",
    )

    return redirect("user_list")