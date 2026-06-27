from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def sync_superuser_profile(sender, instance, **kwargs):
    if not instance.is_superuser:
        return
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    if profile.role != UserProfile.Role.SAAS_ADMIN or profile.gym_id is not None:
        profile.role = UserProfile.Role.SAAS_ADMIN
        profile.gym = None
        profile.save(update_fields=["role", "gym"])
