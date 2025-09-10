from django.db import models
from zoneinfo import available_timezones
import uuid
from django.conf import settings


class Enterprise(models.Model):
    name = models.CharField(max_length=250, verbose_name="название предприятия")
    city = models.CharField(max_length=250, verbose_name="город")
    phone = models.CharField(max_length=20, verbose_name="телефон")
    email = models.EmailField(verbose_name="email")
    website = models.URLField(blank=True, verbose_name="веб-сайт")
    timezone = models.CharField(
        max_length=50,
        choices=sorted([(tz, tz) for tz in available_timezones()]),
        default=settings.TIME_ZONE,
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        indexes = [models.Index(fields=["id"]), models.Index(fields=["uuid"])]

    def __str__(self):
        return f"{self.name}"
