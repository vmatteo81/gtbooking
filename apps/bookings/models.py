from django.conf import settings
from django.db import models


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confermata"
        CANCELLED = "CANCELLED", "Cancellata"
        WAITLIST = "WAITLIST", "Lista d'attesa"
        NO_SHOW = "NO_SHOW", "Assente"

    gym = models.ForeignKey(
        "gyms.Gym",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    session = models.ForeignKey(
        "courses.CourseSession",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    status = models.CharField(
        "Stato",
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Prenotazione"
        verbose_name_plural = "Prenotazioni"
        constraints = [
            models.UniqueConstraint(
                fields=["session", "user"],
                name="uniq_booking_session_user",
            ),
        ]

    def __str__(self):
        return f"{self.user} → {self.session} ({self.get_status_display()})"
