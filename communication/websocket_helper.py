import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

User = get_user_model()


class WebSocketHelper:

    @staticmethod
    def send_page_to_user(user: User, page: str, data: dict):
        group_name = f"user_{user.id}"

        # Get the channel layer
        channel_layer = get_channel_layer()
        json_request = {
            "page": page,
            "data": data,
        }

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_component",
                "message": json.dumps(json_request),
            }
        )
