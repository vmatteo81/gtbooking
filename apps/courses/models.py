from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "BEGINNER", "Principiante"
        INTERMEDIATE = "INTERMEDIATE", "Intermedio"
        ADVANCED = "ADVANCED", "Avanzato"

    gym = models.ForeignKey(
        "gyms.Gym",
        on_delete=models.CASCADE,
        related_name="courses",
    )
    name = models.CharField("Nome", max_length=200)
    description = models.TextField("Descrizione", blank=True)
    duration = models.DurationField("Durata")
    level = models.CharField(
        "Livello",
        max_length=20,
        choices=Level.choices,
        default=Level.BEGINNER,
    )
    instructor_name = models.CharField("Istruttore", max_length=200, blank=True)
    default_capacity = models.PositiveSmallIntegerField("Capienza default", default=10)
    is_active = models.BooleanField("Attivo", default=True)
    created_at = models.DateTimeField("Creato il", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Corso"
        verbose_name_plural = "Corsi"

    def __str__(self):
        return self.name


class CourseSession(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Programmata"
        CANCELLED = "CANCELLED", "Annullata"
        COMPLETED = "COMPLETED", "Completata"

    gym = models.ForeignKey(
        "gyms.Gym",
        on_delete=models.CASCADE,
        related_name="course_sessions",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    starts_at = models.DateTimeField("Inizio")
    ends_at = models.DateTimeField("Fine")
    capacity = models.PositiveSmallIntegerField(
        "Capienza",
        null=True,
        blank=True,
        help_text="Vuoto = usa capienza default del corso",
    )
    status = models.CharField(
        "Stato",
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        verbose_name = "Sessione"
        verbose_name_plural = "Sessioni"
        constraints = [
            models.CheckConstraint(
                check=Q(ends_at__gt=F("starts_at")),
                name="coursesession_ends_after_starts",
            ),
            models.CheckConstraint(
                check=Q(capacity__isnull=True) | Q(capacity__gt=0),
                name="coursesession_capacity_positive_or_null",
            ),
        ]

    def __str__(self):
        return f"{self.course.name} @ {self.starts_at}"

    def clean(self):
        super().clean()
        if self.course_id and self.gym_id and self.course.gym_id != self.gym_id:
            raise ValidationError("La palestra della sessione deve coincidere con quella del corso.")

    def save(self, *args, **kwargs):
        if self.course_id:
            self.gym_id = self.course.gym_id
        super().save(*args, **kwargs)

    def effective_capacity(self):
        if self.capacity is not None:
            return self.capacity
        return self.course.default_capacity
