from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Device
from .serializers import DeviceModelSerializer

# Create your views here.


class DeviceRegisterView(GenericAPIView):
    serializer_class = DeviceModelSerializer

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(data={
            "code": 0,
            "msg": "success",
            "data": ser.data
        })
