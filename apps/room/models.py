from collections import defaultdict

from django.db import models

from apps.device.models import Device

# Create your models here.
from apps.room.poke import PokerGame, GameState


def default_game():
    game = PokerGame()
    game.state = GameState()
    return game


STATES = defaultdict(default_game)

class Room(models.Model):
    class Status(models.TextChoices):
        WAITING = 'waiting'
        PLAYING = 'playing'
        FINISHED = 'finished'

    table = models.ForeignKey('device.Device', on_delete=models.CASCADE, null=True, blank=True)
    player_count = models.IntegerField()  # 2 - 8
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.WAITING,
    )
    state = models.JSONField(default={})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def game_state(self):
        return STATES[self.id]

    def add_player(self, device: Device, index: int):
        if index < 1 or index > self.player_count:
            raise ValueError("index should be in range 2-8")
        if device.type == Device.Type.TABLET:
            raise ValueError("tablet can not be a player")
        if self.player_set.filter(index=index).exists():
            raise ValueError("player already exists")
        if self.status != Room.Status.WAITING:
            raise ValueError(f"room {self.status} status at {self.created_at}")

        Player.objects.create(room=self, device=device, index=index)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Room'


class Player(models.Model):
    class Status(models.TextChoices):
        ONLINE = "online"
        OFFLINE = "offline"
        EXIT = "exit"
        LOSE = "lose"
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    index = models.IntegerField(default=1)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OFFLINE,
    )
    channel_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"player {self.index} of room {self.room.name}"

    class Meta:
        verbose_name = 'RoomPlayer'
        unique_together = (
            ('room','index')
            ('room','device')
        ),
