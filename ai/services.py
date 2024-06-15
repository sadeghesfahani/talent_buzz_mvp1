from django.conf import settings
from django.contrib.auth import get_user_model
from openai import OpenAI
from openai.types.beta.threads import Run

from honeycomb.honeycomb_service import HiveService
from .helpers import AIBaseClass
from .models import Message

User = get_user_model()
client = OpenAI(api_key=settings.OPEN_AI_API_KEY)


class AIService:
    def __init__(self, user: User, assistant_type: str):
        self.last_message = None
        self.user = user
        self.ai = AIBaseClass(assistant_type)
        self.hive_service = HiveService()
        self.thread_id = self.ai.get_or_create_thread_by_user(user).id

    def send_message(self, message: str, additional_instructions: str = "",
                     ai_type: str = "general_assistant"):
        self.last_message = Message.objects.create(message=message, user=self.user)
        hives = self.hive_service.get_user_hives(self.user)
        vector_stores = [self.ai.base_vector_store, ]

        if ai_type == "hive_assistant":
            for hive in hives:
                vector_stores.append(self.ai.get_hive_tools(hive.id).get_or_create_hive_vector_store(hive.id))

        thread = self.ai.get_or_create_thread(self.thread_id)
        thread = client.beta.threads.update(
            self.thread_id,
            tool_resources={
                "file_search": {"vector_store_ids": [vector_store.id for vector_store in vector_stores]}},
            metadata=thread.metadata
        )
        self.ai.add_message_to_thread(thread.id, message)
        run = self.ai.run(self.ai.get_assistant(ai_type).id, thread.id, additional_instructions)
        return self.process_ai_response(run)

    def process_ai_response(self, run: Run):
        if run.status == "completed":
            response = client.beta.threads.messages.list(thread_id=run.thread_id)[-1]
            self.last_message.response = response.content
            return response.content
