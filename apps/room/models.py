from django.db import models

from apps.device.models import Device

# Create your models here.


class Room(models.Model):
    class Status(models.TextChoices):
        WAITING = 'waiting'
        PLAYING = 'playing'
        FINISHED = 'finished'
    name = models.CharField(max_length=100)
    table = models.OneToOneField('device.Device', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.WAITING,
    )

    def add_player(self, device: Device, index: int):
        if index < 2 or index > 8:
            raise ValueError("index should be in range 2-8")
        if self.player_set.filter(index=index).exists():
            raise ValueError("player already exists")
        if self.status != Room.Status.WAITING:
            raise ValueError(f"room in {self.status} status")
        Player.objects.create(room=self, device=device, index=index)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Room'


class Player(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    index = models.IntegerField(default=2)

    def __str__(self):
        return f"player {self.index} of room {self.room.name}"

    class Meta:
        verbose_name = 'RoomPlayer'
        unique_together = (
            ('room','index')
            ('room','device')
        ),
