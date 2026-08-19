from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver


User = get_user_model()


@receiver(post_save, sender=User)
def update_password_setup_status(
    sender,
    instance,
    **kwargs,
):

    profile = getattr(
        instance,
        "profile",
        None,
    )

    if not profile:
        return

    if (
        instance.has_usable_password()
        and not profile.password_setup_completed
    ):

        profile.password_setup_completed = True

        profile.save(
            update_fields=[
                "password_setup_completed"
            ]
        )