from django.conf import settings
from django.contrib.auth.models import User
from openai import OpenAI
from openai.types.beta import VectorStore, Assistant, Thread
from openai.types.beta.threads import Run
from .models import Thread as ThreadModel
import honeycomb.honeycomb_service
from ai.models import AssistantInfo


class AIBaseClass:
    def __init__(self, assistant_type="general_assistant"):
        self.tools = None
        self.client = OpenAI(api_key=settings.OPEN_AI_API_KEY)
        self.base_vector_store = None
        self.functions = []
        self.assistant_info = self.get_or_create_assistant_info_model_object()
        self.assistant = self.get_assistant(assistant_type)

    def get_hive_tools(self, hive_id: str) -> 'HiveAI':
        if self.tools:
            return self.tools
        else:
            self.tools = HiveAI(self, hive_id)
            return self.tools

    def get_or_create_vector_store(self, vector_store_id: str) -> VectorStore:
        if vector_store_id:
            return self.client.beta.vector_stores.create()
        else:
            return self.client.beta.vector_stores.retrieve(vector_store_id)

    def add_files_to_vector_store(self, file_ids: [str], vector_store_id: str) -> VectorStore:
        self.client.beta.vector_stores.file_batches.create(
            vector_store_id=vector_store_id,
            file_ids=file_ids
        )

        return self.get_or_create_vector_store(vector_store_id)

    def add_file_to_vector_store(self, file_id: str, vector_store_id: str) -> VectorStore:
        self.client.beta.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_id
        )

        return self.get_or_create_vector_store(vector_store_id)

    def remove_file_from_vector_store(self, file_id: str, vector_store_id: str) -> VectorStore:
        self.client.beta.vector_stores.files.delete(
            vector_store_id=vector_store_id,
            file_id=file_id
        )

        return self.get_or_create_vector_store(vector_store_id)

    @staticmethod
    def get_or_create_assistant_info_model_object() -> AssistantInfo:
        if AssistantInfo.objects.count() < 1:
            return AssistantInfo.objects.create()
        else:
            return AssistantInfo.objects.first()

    def get_or_create_thread(self, thread_id) -> Thread:
        if not thread_id:
            return self.client.beta.threads.create()
        else:
            return self.client.beta.threads.retrieve(thread_id)

    def get_or_create_thread_by_user(self, user: User) -> Thread:
        thread_model_object = ThreadModel.objects.filter(user=user).first()
        if thread_model_object:
            return self.client.beta.threads.retrieve(thread_model_object.thread_id)
        else:
            thread = self.client.beta.threads.create()
            ThreadModel.objects.create(user=user, thread_id=thread.id)
            return thread


    def run(self, assistant_id: str, thread_id: str, additional_instructions: str = "") -> Run:
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            additional_instructions=additional_instructions
        )
        return run

    def add_message_to_thread(self, thread_id: str, message: str) -> Thread:
        thread = self.client.beta.threads.retrieve(thread_id)
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            content=message,
            role="user"
        )

        return thread

    def get_assistant(self, model: str) -> Assistant:
        if model == "general_assistant":
            return self.client.beta.assistants.retrieve(self.assistant_info.general_assistant_id)
        elif model == "hive_assistant":
            return self.client.beta.assistants.retrieve(self.assistant_info.hive_assistant_id)
        else:
            return self.client.beta.assistants.retrieve(self.assistant_info.backend_assistant_id)


class HiveAI:
    def __init__(self, ai_base_class: AIBaseClass, hive_id: str):
        self.hive_id = hive_id
        self.ai_base_class = ai_base_class
        self.vector_store = self.get_or_create_hive_vector_store(hive_id)

    def get_or_create_hive_vector_store(self, hive_id: str) -> VectorStore:
        hive_object = honeycomb.honeycomb_service.HiveService.get_hive(hive_id)
        return self.ai_base_class.get_or_create_vector_store(
            hive_object.vector_store_id if hive_object.vector_store_id else None)



