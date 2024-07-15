from django.urls import path

from . import views


app_name = "device"


urlpatterns = [
    path("register/", views.DeviceRegisterView.as_view(), name="register"),
]
