# chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Personal chat WebSocket route
    re_path(r'ws/(?P<room_name>[\w-]+)/$', consumers.ChatConsumer.as_asgi()),
    
    # Group chat WebSocket route
    re_path(r'ws/group/(?P<group_id>[\w-]+)/$', consumers.GroupChatConsumer.as_asgi()),
]