from django.urls import re_path
from . import users

websocket_urlpatterns = [
    re_path(r'ws/(?P<room_name>\w+)/$', users.ChatConsumer.as_asgi()),
    re_path(r'ws/receiver/(?P<room_name>\w+)/$', users.ChatConsumer.as_asgi()),
]