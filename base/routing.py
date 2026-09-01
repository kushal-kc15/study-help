from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/room/(?P<room_id>[0-9]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/dm/(?P<user_id>[0-9]+)/$', consumers.DMConsumer.as_asgi()),
    re_path(r'ws/presence/$', consumers.PresenceConsumer.as_asgi()),
]
