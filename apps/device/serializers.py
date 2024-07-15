from rest_framework import serializers

from .models import Device


class DeviceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'
