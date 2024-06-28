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

    @staticmethod
    def send_notification(user: User, message: str):
        group_name = f"user_notification_{user.id}"

        # Get the channel layer
        channel_layer = get_channel_layer()
        json_request = {
            "message": message,
        }

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "message": json.dumps(json_request),
            }
        )

    @staticmethod
    def send_message_to_conversation(message: 'Message'):
        from communication.models import Message
        group_name = f"chat_{message.conversation.id}"
        data = {
            "message": message.content,
            "sender": message.sender.id,
            "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "document": message.document.document.path if message.document else None,
        }

        # Get the channel layer
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_message",
                "message": json.dumps(data),
            }
        )
