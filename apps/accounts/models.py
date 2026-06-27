from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Cliente"
        GYM_STAFF = "GYM_STAFF", "Staff palestra"
        SAAS_ADMIN = "SAAS_ADMIN", "Admin SaaS"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        "Ruolo",
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    gym = models.ForeignKey(
        "gyms.Gym",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="profiles",
    )

    class Meta:
        verbose_name = "Profilo utente"
        verbose_name_plural = "Profili utente"

    def __str__(self):
        return f"{self.user.get_username()} ({self.get_role_display()})"

    def clean(self):
        super().clean()
        if self.role == self.Role.SAAS_ADMIN:
            if self.gym_id is not None:
                raise ValidationError({"gym": "L'admin SaaS non deve essere associato a una palestra."})
        elif self.gym_id is None:
            raise ValidationError({"gym": "Cliente e staff devono avere una palestra."})
