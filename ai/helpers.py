import asyncio
import time
from typing import Literal

from django.conf import settings
from django.db.models import QuerySet
from openai import OpenAI
from openai.types.beta import VectorStore, Assistant, Thread
from openai.types.beta.threads import Run

import honeycomb.honeycomb_service
from common.models import Document
from .models import Thread as ThreadModel

client = OpenAI(api_key=settings.OPEN_AI_API_KEY)


class AIBaseClass:
    def __init__(self, assistant_type="general_assistant"):
        self.tools = None
        self.client = OpenAI(api_key=settings.OPEN_AI_API_KEY)
        self.assistant_info = self.get_or_create_assistant_info_model_object()
        self.base_vector_store = self.assistant_info.base_vector_store_id
        self.functions = []

        self.assistant = self.get_assistant(assistant_type)

    @staticmethod
    def get_translation(audio_file) -> str:

        transcript = client.audio.translations.create(
            model="whisper-1",
            file=("transcript.mp3", audio_file, 'audio/mpeg'),
        )
        return transcript.text

    @staticmethod
    def generate_audio(text: str, voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "alloy"):
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
        )
        return response

    def get_new_file_ids(self, vector_store_id, document_queryset: QuerySet[Document]) -> [str]:
        """
        Retrieve new file IDs that are not already in the vector store.

        :param vector_store_id: The ID of the vector store.
        :param document_queryset: QuerySet of documents to check.
        :return: List of new file IDs.
        """
        supported_extensions = ['pdf', 'txt', 'docx']  # Add all supported extensions here

        file_ids = []
        for document in document_queryset:
            file_extension = document.document.file.name.split('.')[-1].lower()
            if file_extension not in supported_extensions:
                print(
                    f"Unsupported file extension: {file_extension} for document {document.document.file.name} - {document.document.id}")
                continue

            file_ids.append(document.file_id)

        # Distinct file_ids
        file_ids = list(set(file_ids))

        # Retrieve existing file IDs from the vector store
        try:
            existing_files_page = self.client.beta.vector_stores.files.list(vector_store_id=vector_store_id)
            existing_file_ids = {file.id for file in existing_files_page}
        except Exception as e:
            print(f"Failed to retrieve existing files from vector store: {e}")
            return []

        # Filter out the file IDs that are already in the vector store
        new_file_ids = [file_id for file_id in file_ids if file_id not in existing_file_ids]

        return new_file_ids

    def add_documents_to_vector_store(self, vector_store_id, document_queryset):
        """
        Add documents to the vector store.

        :param vector_store_id: The ID of the vector store.
        :param document_queryset: QuerySet of documents to add.
        :return: None
        """

        new_file_ids = self.get_new_file_ids(vector_store_id, document_queryset)
        if new_file_ids:
            asyncio.run(add_files_async(vector_store_id, new_file_ids))
        else:
            print("No new files to add to vector store")

    def get_hive_tools(self, hive_id: str) -> 'HiveAI':
        if self.tools:
            return self.tools
        else:
            self.tools = HiveAI(self, hive_id)
            return self.tools

    def get_or_create_vector_store(self, vector_store_id: str) -> VectorStore:
        if not vector_store_id:
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
    def get_or_create_assistant_info_model_object() -> 'AssistantInfo':
        from ai.models import AssistantInfo
        if AssistantInfo.objects.count() < 1:
            return AssistantInfo.objects.create()
        else:
            return AssistantInfo.objects.first()

    def get_or_create_thread(self, thread_id) -> Thread:
        if not thread_id:
            return self.client.beta.threads.create()
        else:
            return self.client.beta.threads.retrieve(thread_id)

    def get_or_create_thread_by_user(self, user: 'User') -> Thread:
        thread_model_object = ThreadModel.objects.filter(user=user).first()
        if thread_model_object:
            return self.client.beta.threads.retrieve(thread_model_object.thread_id)
        else:
            thread = self.client.beta.threads.create()
            ThreadModel.objects.create(user=user, thread_id=thread.id)
            return thread

    def run(self, assistant_id: str, thread_id: str, additional_instructions: str = "") -> Run:
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
            additional_instructions=additional_instructions
        )
        return run

    def add_message_to_thread(self, thread_id: str, message: str) -> Thread:
        # try:
        #     print("canceling existing run")
        #     self.client.beta.threads.runs.cancel(thread_id=thread_id, run_id="run_EVZOB6zC8ODtkNGr2utZZmKm")
        #     print("Cancelled existing run")
        # except Exception as e:
        #     print(f"Failed to cancel existing run: {e}")
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


async def add_files_async(vector_store_id, file_ids):
    tasks = []
    for file_id in file_ids:
        task = asyncio.create_task(create_file(vector_store_id, file_id))
        tasks.append(task)

    await asyncio.gather(*tasks)


async def create_file(vector_store_id, file_id):
    from django.conf import settings
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPEN_AI_API_KEY)
    print(f"Adding file {file_id} to vector store {vector_store_id}")
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, lambda: client.beta.vector_stores.files.create_and_poll(
            vector_store_id=vector_store_id, file_id=file_id))
        print(f"Successfully added file {file_id} to vector store")
    except Exception as e:
        print(f"Failed to add file {file_id} to vector store: {e}")
        raise e


async def create_file(vector_store_id, file_id):
    loop = asyncio.get_event_loop()
    client = OpenAI(api_key=settings.OPEN_AI_API_KEY)

    try:
        await loop.run_in_executor(None, lambda: client.beta.vector_stores.files.create_and_poll(
            vector_store_id=vector_store_id, file_id=file_id))
        print(f"Successfully initiated upload for file {file_id}")

        # Polling until the file becomes available
        await poll_file_availability(vector_store_id, file_id)

        print(f"File {file_id} is now available in vector store")
    except Exception as e:
        print(f"Failed to add file {file_id} to vector store: {e}")


async def poll_file_availability(vector_store_id, file_id, timeout=20, poll_interval=2):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Replace this with the actual method to check if the file is available
            file = client.beta.vector_stores.files.retrieve(vector_store_id=vector_store_id, file_id=file_id)
            if file and file.status == 'completed':  # Assuming 'available' is the status you are checking for
                return file
        except Exception as e:
            print(f"Waiting for file {file_id} to become available: {e}")

        await asyncio.sleep(poll_interval)
    raise TimeoutError(f"File {file_id} did not become available within {timeout} seconds.")
