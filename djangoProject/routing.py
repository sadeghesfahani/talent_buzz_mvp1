from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/ai/$', consumers.FrontEndConsumer.as_asgi()),
    re_path(r'ws/notification/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/conversation/(?P<conversation_id>\d+)/$', consumers.ConversationConsumer.as_asgi()),
]
