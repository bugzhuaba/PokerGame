from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework import serializers

from apps.device.models import Device
from apps.room.models import Room


class RoomSerializer(serializers.ModelSerializer):
    player_count = serializers.IntegerField(validators=[
        MinValueValidator(2, message="min player count is 2"),
        MaxValueValidator(8, message="max player count is 8")
    ])
    table = serializers.CharField()

    def valiadate_table(self, table):
        is_tablet = table.startswith("tablet")
        if is_tablet:
            device_type = Device.Type.TABLET
        else:
            device_type = Device.Type.MOBILE
        table, created = Device.objects.get_or_create(device_id=table, type=device_type)
        if table is not None and table.type != Device.Type.TABLET:
            raise serializers.ValidationError("a tablet is required to create a room")
        return table

    class Meta:
        model = Room
        fields = ("player_count", "table")


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["name", "device_id"]


class RoomDetailSerializer(serializers.ModelSerializer):
    players = DeviceSerializer(many=True, read_only=True, source="player_set")

    class Meta:
        model = Room
        fields = ["player_count", "status", "players"]


class JoinRoomSerializer(serializers.Serializer):
    index = serializers.IntegerField()
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    mobile = serializers.PrimaryKeyRelatedField(queryset=Device.objects.filter(type=Device.Type.MOBILE))

    def validate_room(self, room):
        if room.status != Room.Status.WAITING:
            raise serializers.ValidationError("room is not waiting")
        return room

    def validate_mobile(self, mobile):
        if Room.objects.filter(player_set__device=mobile).exists():
            raise serializers.ValidationError("device already joined")
        return mobile

    def validate(self, attrs):
        room: Room = attrs["room"]
        device: Device = attrs["mobile"]
        index = attrs["index"]

        if index < 1 or index > room.player_count:
            raise serializers.ValidationError(f"index should be in range 1-{self.index}")

        if room.player_set.filter(index=attrs["index"]).exists():
            raise serializers.ValidationError("player already exists")

        if room.player_set.filter(device=device).exists():
            raise serializers.ValidationError("device already joined")
        return attrs


class LeaveRoomSerializer(serializers.Serializer):
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())
    mobile = serializers.PrimaryKeyRelatedField(queryset=Device.objects.filter(type=Device.Type.MOBILE))

    def validate_room(self, room):
        if room.status != Room.Status.WAITING:
            raise serializers.ValidationError("only waiting room can leave")
        return room

    def validate_mobile(self, mobile):
        if not Room.objects.filter(player_set__device=mobile).exists():
            raise serializers.ValidationError("device not joined")
        return mobile
