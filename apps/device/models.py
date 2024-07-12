from django.db import models

# Create your models here.


class Device(models.Model):
    class Type(models.TextChoices):
        TABLET = 'tablet'
        MOBILE = 'mobile'
    device_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=10,
        choices=Type.choices,
        default=Type.MOBILE,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Device'
