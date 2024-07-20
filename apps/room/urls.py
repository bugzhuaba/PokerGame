from django.urls import path

from . import views


app_name = "room"


urlpatterns = [
    path("create/", views.CreateRoomView.as_view(), name="create"),
    path("detail/<int:pk>/", views.RoomDetailView.as_view(), name="room"),
    path("join/", views.JoinRoomView.as_view(), name="join"),
    path("leave/", views.LeaveRoomView.as_view(), name="leave")
]
