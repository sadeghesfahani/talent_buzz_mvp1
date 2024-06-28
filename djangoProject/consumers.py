import json

import magic
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("hi")
        await self.accept()
        print("accepted")

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))


class FrontEndConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if the user is authenticated
        if self.scope["user"].is_authenticated:
            # Use the user's ID to create a unique group name
            self.room_group_name = f"user_{self.scope['user'].id}"

            # Join the user to their unique group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        # Leave the group on disconnect
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            # Check if the received file is a voice file
            if self.is_voice_file(bytes_data):
                await self.handle_voice_file(bytes_data)
            else:
                await self.send(text_data="Invalid file type.")
        if text_data:
            pass

    def is_voice_file(self, bytes_data):
        # Use python-magic to detect the MIME type of the file
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(bytes_data)
        print("File type", file_type)
        return file_type.startswith('audio/')

    async def handle_voice_file(self, bytes_data):
        from ai.helpers import AIBaseClass
        from ai.services import AIService
        user = self.scope['user']
        text = await self.convert_speech_to_text(bytes_data)
        if user.is_superuser:
            ai_service = await sync_to_async(AIService)(user, 'backend_assistant')
            response = await sync_to_async(ai_service.send_message)(text)
            print("Response", response)
            voice = AIBaseClass.generate_audio(response)
            await self.send_file_to_client(voice.content)
        else:
            response = await sync_to_async(AIService(user, 'backend_assistant').send_message)(text)
            await self.send(text_data=response)

    async def convert_speech_to_text(self, file) -> str:
        from ai.helpers import AIBaseClass
        return AIBaseClass.get_translation(file)

    async def send_file_to_client(self, voice):
        # Read the file in binary mode
        await self.send(bytes_data=voice)

    async def send_component(self, data: dict):
        await self.send(text_data=json.dumps(data, indent=4))
