from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


ROLE_LEVELS = {
    "viewer": 1,
    "officer": 2,
    "manager": 3,
    "supply_chain_manager": 4,
    "admin": 5,
}


def department_required(*allowed_departments):
    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            user = request.user

            if not user.is_authenticated:
                return redirect("login")

            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            profile = getattr(user, "profile", None)

            if not profile:
                messages.error(
                    request,
                    "Your account has no assigned profile.",
                )
                return redirect("home")

            if profile.role in [
                "admin",
                "supply_chain_manager",
            ]:
                return view_func(request, *args, **kwargs)

            if profile.department not in allowed_departments:
                messages.error(
                    request,
                    "You do not have permission to access this department.",
                )
                return redirect("home")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def role_required(minimum_role):
    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            user = request.user

            if not user.is_authenticated:
                return redirect("login")

            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            profile = getattr(user, "profile", None)

            if not profile:
                messages.error(
                    request,
                    "Your account has no assigned role.",
                )
                return redirect("home")

            user_level = ROLE_LEVELS.get(
                profile.role,
                0,
            )

            required_level = ROLE_LEVELS.get(
                minimum_role,
                999,
            )

            if user_level < required_level:
                messages.error(
                    request,
                    "Your role does not allow this action.",
                )
                return redirect("home")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator