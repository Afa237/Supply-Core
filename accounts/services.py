from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_staff_invitation(request, user):

    profile = user.profile

    uid = urlsafe_base64_encode(
        force_bytes(user.pk)
    )

    token = default_token_generator.make_token(
        user
    )

    reset_path = reverse(
        "password_reset_confirm",
        kwargs={
            "uidb64": uid,
            "token": token,
        },
    )

    setup_url = request.build_absolute_uri(
        reset_path
    )

    subject = "Your Supply Core account is ready"

    message = f"""
Hello {user.first_name or user.username},

A Supply Core account has been created for you.

Username: {user.username}

Department: {profile.get_department_display()}
Role: {profile.get_role_display()}

Use the secure link below to create your password:

{setup_url}

If you were not expecting this invitation,
please contact your Supply Core administrator.

For security, do not share this link.

Supply Core
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    profile.invitation_sent_at = timezone.now()

    profile.save(
        update_fields=["invitation_sent_at"]
    )