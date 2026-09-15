COMPANY_WIDE_ROLES = {"admin", "supply_chain_manager"}


def filter_by_user_scope(queryset, user, branch_field="branch"):
    """Restrict a queryset according to the user's company/branch access.

    Superuser:
        Sees everything.

    Admin / Supply Chain Manager:
        Sees all branches belonging to their company.

    Manager / Officer / Viewer:
        Sees only their assigned branch.
    """
    if user.is_superuser:
        return queryset

    profile = getattr(user, "profile", None)

    if not profile:
        return queryset.none()

    if not profile.company:
        return queryset.none()

    # Company-wide users
    if profile.role in COMPANY_WIDE_ROLES:
        lookup = {
            f"{branch_field}__company": profile.company
        }
        return queryset.filter(**lookup)

    # Branch-level users
    if not profile.branch:
        return queryset.none()

    lookup = {
        branch_field: profile.branch
    }

    return queryset.filter(**lookup)