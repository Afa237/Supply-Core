from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from . import admin_view


urlpatterns = [

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "register/",
        views.register_view,
        name="register",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),
    path(
        "users/",
        admin_view.user_list,
        name="user_list",
    ),
    path(
        "users/create/",
        admin_view.user_create,
        name="user_create",
    ),
    path(
        "users/<int:user_id>/update/",
        admin_view.user_update,
        name="user_update",
    ),
    path(
        "users/<int:user_id>/resend-invitation/",
        admin_view.resend_invitation,
        name="resend_invitation",
    ),

    # Forgot password
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
        ),
        name="password_reset",
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),

    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/accounts/reset/done/",
        ),
        name="password_reset_confirm",
    ),

    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]