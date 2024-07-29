from django.urls import path

from apps.room.consumers import GameConsumer

websocket_urlpatterns = [
    path('ws/game/<slug:room_id>/', GameConsumer.as_asgi()),
]
