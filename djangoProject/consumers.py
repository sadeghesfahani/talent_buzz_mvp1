import json

import magic
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class BaseConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.room_group_name = self.generate_room_group_name()
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    def generate_room_group_name(self):
        raise NotImplementedError("Subclasses must implement this method.")


class FrontEndConsumer(BaseConsumer):

    def generate_room_group_name(self):
        return f"user_{self.scope['user'].id}"

    async def receive(self, text_data=None, bytes_data=None):
        from ai.helpers import AIBaseClass
        from ai.services import AIService
        print("Received data")
        if bytes_data:
            # Check if the received file is a voice file
            if self.is_voice_file(bytes_data):
                await self.handle_voice_file(bytes_data)
            else:
                await self.send(text_data="Invalid file type.")
        if text_data:
            user = self.scope['user']
            # Handle the text data
            ai_service = await sync_to_async(AIService)(user, 'backend_assistant')
            print("Text data", text_data)
            response = await sync_to_async(ai_service.send_message)(text_data)
            voice = AIBaseClass.generate_audio(response)
            await self.send_file_to_client(voice.content)
            await self.send(text_data=response)

    def is_voice_file(self, bytes_data):
        # Use python-magic to detect the MIME type of the file
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(bytes_data)
        print("File type", file_type)
        return file_type.startswith("audio")

    async def handle_voice_file(self, bytes_data):
        from ai.helpers import AIBaseClass
        from ai.services import AIService
        user = self.scope['user']
        text = await self.convert_speech_to_text(bytes_data)
        if user.is_superuser:
            ai_service = await sync_to_async(AIService)(user, 'backend_assistant')
            response = await sync_to_async(ai_service.send_message)(text)
            voice = AIBaseClass.generate_audio(response)
            await self.send_file_to_client(voice.content)
        else:
            ai_service = await sync_to_async(AIService)(user, 'backend_assistant')
            response = await sync_to_async(ai_service.send_message)(text)
            voice = AIBaseClass.generate_audio(response)
            await self.send_file_to_client(voice.content)
            await self.send(text_data=response)

    async def convert_speech_to_text(self, file) -> str:
        from ai.helpers import AIBaseClass
        return AIBaseClass.get_translation(file)

    async def send_file_to_client(self, voice):
        # Read the file in binary mode
        await self.send(bytes_data=voice)

    async def send_component(self, data: dict):
        await self.send(text_data=json.dumps(data, indent=4))


class NotificationConsumer(BaseConsumer):

    def generate_room_group_name(self):
        return f"user_notification_{self.scope['user'].id}"

    async def receive(self, text_data=None, bytes_data=None):
        # it shouldn't receive any message
        pass

    async def send_notification(self, data: dict):
        await self.send(text_data=json.dumps(data, indent=4))


class ConversationConsumer(BaseConsumer):

    def generate_room_group_name(self):
        return f"chat_{self.scope['url_route']['kwargs']['conversation_id']}"

    async def receive(self, text_data=None, bytes_data=None):
        # it shouldn't receive any message
        pass

    async def send_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))
