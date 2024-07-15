from django.db import models

# Create your models here.


class Device(models.Model):
    class Type(models.TextChoices):
        TABLET = 'tablet'
        MOBILE = 'mobile'

    class DeviceStatus(models.TextChoices):
        ONLINE = 'online'
        OFFLINE = 'offline'

    device_id = models.CharField(max_length=100, primary_key=True, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)

    type = models.CharField(
        max_length=10,
        choices=Type.choices,
        default=Type.MOBILE,
    )

    status = models.CharField(
        max_length=10,
        choices=DeviceStatus.choices,
        default=DeviceStatus.ONLINE,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Device'
