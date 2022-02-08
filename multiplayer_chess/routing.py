from django.urls import re_path, path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/multiplayer_chess/gameroom/random', consumers.RandomMatchConsumer.as_asgi()),
    path('ws/multiplayer_chess/gameroom/friend/<str:friend_name>', consumers.FriendMatchConsumer.as_asgi()),
    path('ws/multiplayer_chess/home', consumers.HomeConsumer.as_asgi()),
]