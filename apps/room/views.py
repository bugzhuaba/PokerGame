from django.shortcuts import render

# Create your views here.
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.response import Response

from apps.room.models import Room
from apps.room.serializers import RoomSerializer, JoinRoomSerializer, LeaveRoomSerializer


class CreateRoomView(GenericAPIView):
    serializer_class = RoomSerializer

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(data={
            "code": 0,
            "msg": "success",
            "data": ser.data
        })
class RoomDetailView(RetrieveAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.all()

class JoinRoomView(GenericAPIView):
    serializer_class = JoinRoomSerializer

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()

        room = ser.validated_data["room"]
        mobile = ser.validated_data["mobile"]
        room.add_player(mobile, ser.validated_data["index"])

        return Response(data={
            "code": 0,
            "msg": "success",
            "data": ser.data
        })

class LeaveRoomView(GenericAPIView):
    serializer_class = LeaveRoomSerializer

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        room = ser.validated_data["room"]
        mobile = ser.validated_data["mobile"]
        room.player_set.filter(device=mobile).delete()

        return Response(data={
            "code": 0,
            "msg": "success",
            "data": ser.data
        })