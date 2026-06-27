from django.db import models


class Gym(models.Model):
    name = models.CharField("Nome", max_length=200)
    slug = models.SlugField("Slug", max_length=80, unique=True)
    is_active = models.BooleanField("Attiva", default=True)
    created_at = models.DateTimeField("Creata il", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Palestra"
        verbose_name_plural = "Palestre"

    def __str__(self):
        return self.name
