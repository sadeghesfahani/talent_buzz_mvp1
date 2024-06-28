import json

from django.conf import settings
from django.contrib.auth import get_user_model
from openai import OpenAI

from common.models import Document
from communication.websocket_helper import WebSocketHelper
from honeycomb.honeycomb_service import HiveService, BeeService, NectarService
from honeycomb.serializers import BeeSerializer, BeeWithDetailSerializer, NectarSerializer
from user.services import UserService
from .helpers import AIBaseClass
from .models import Message, Thread
from .serializers import HiveSerializer

User = get_user_model()
client = OpenAI(api_key=settings.OPEN_AI_API_KEY)


def create_user(email, first_name, last_name, phone_number="", skills=None, certificates=None, education=None, bio=None,
                tags=None, file_id="",
                **extra_fields):
    if certificates is None:
        certificates = []
    print(
        f"Creating user with email: {email}, first_name: {first_name}, last_name: {last_name}, phone_number: {phone_number}, skills: {skills}, certificates: {certificates}, education: {education}, bio: {bio}, tags: {tags}, file_id: {file_id}")
    try:
        user = UserService.create_user(email, first_name, last_name, phone_number, skills, certificates, education, bio,
                                       tags)
    except Exception as e:
        print(f"Error creating user: {e}")
        return f"Error creating user: {e}"
    document = Document.objects.get(file_id=file_id)
    BeeService.create_bee(user=user, bio=bio, document_id=document.id)
    return f"User created successfully. User ID: {user.id}"


class AIService:
    def __init__(self, user: User, assistant_type: str):
        self.last_message = None
        self.user = user
        self.ai = AIBaseClass(assistant_type)
        self.hive_service = HiveService()
        self.bee_service = BeeService()
        self.thread_id = self.ai.get_or_create_thread_by_user(user).id
        self.local_thread_id = self.get_or_create_local_thread_by_user(user).id

    def send_message(self, message: str, additional_instructions: str = "",
                     ai_type: str = "general_assistant", vector_stores=None):

        self.last_message = Message.objects.create(content=message, user=self.user, thread_id=self.local_thread_id)
        hives = self.hive_service.get_user_hives(self.user)
        vector_stores = [self.ai.base_vector_store, ] if not vector_stores else vector_stores
        thread = self.ai.get_or_create_thread(self.thread_id)

        thread = client.beta.threads.update(
            self.thread_id,
            tool_resources={
                "file_search": {"vector_store_ids": vector_stores}},
            metadata=thread.metadata
        )
        if ai_type == "backend_assistant":
            thread = client.beta.threads.create(
                tool_resources={
                    "file_search": {"vector_store_ids": vector_stores}},
                metadata=thread.metadata
            )
        self.ai.add_message_to_thread(thread.id, message)
        run = self.ai.run(self.ai.get_assistant(ai_type).id, thread.id, additional_instructions)
        return self.process_ai_response(run)

    def review_document_with_file_id(self, file_id):
        """Send a document for review to the specified assistant using its file_id."""
        document = Document.objects.get(file_id=file_id)
        isolated_vector_store = self.ai.get_or_create_vector_store("")
        document.isolated_vector_store = isolated_vector_store.id
        self.ai.add_documents_to_vector_store(isolated_vector_store.id, [document])

        self.send_message(f"Review this file id: {file_id}", ai_type="backend_assistant",
                          additional_instructions=f'you need to specifically look into the file id {file_id} and call create_user function with the required arguments. note that everything should be in English',
                          vector_stores=[isolated_vector_store.id])

    def process_ai_response(self, run):
        print(run.status)
        if run.status == "requires_action":
            print("here")
            function_responses = list()
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                arguments = tool.function.arguments
                # parse string to dict
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError as e:
                    print(f"Error parsing arguments: {e}")
                    arguments = {}
                _function = self.get_function_reference(tool.function.name)
                try:
                    function_response = _function(**arguments)
                except Exception as e:
                    print(f"Error processing function: {e}")
                    function_response = "Error processing function"
                if isinstance(function_response, str):
                    function_responses.append({
                        "tool_call_id": tool.id,
                        "output": function_response
                    })
                else:
                    function_responses.append({
                        "tool_call_id": tool.id,
                        "output": "Error processing function"
                    })

            return self.process_ai_response(
                client.beta.threads.runs.submit_tool_outputs_and_poll(tool_outputs=function_responses, run_id=run.id,
                                                                      thread_id=run.thread_id))

        elif run.status == "completed":
            response = client.beta.threads.messages.list(thread_id=run.thread_id).data[0]
            self.last_message.response = response.content[0].text.value
            self.last_message.save()
            print(self.last_message.response)
            return self.last_message.response

    def show_bees_to_user(self, bees_id_list: [str]) -> str:
        bees_queryset = self.bee_service.get_bee_queryset(bees_id_list)
        bees = BeeWithDetailSerializer(bees_queryset, many=True)
        WebSocketHelper.send_page_to_user(self.user, "show_bees", bees.data)
        return "data has been shown successfully, user is seeing it on his/her screen"

    def show_hives_to_user(self,hives_id_list: [str]) -> str:
        hives_queryset = self.hive_service.get_hive_queryset(hives_id_list)
        hives = HiveSerializer(hives_queryset, many=True)
        WebSocketHelper.send_page_to_user(self.user, "show_hives", hives.data)
        return "data has been shown successfully, user is seeing it on his/her screen"

    def show_nectars_to_user(self, nectars_id_list: [str]) -> str:
        nectars_queryset = NectarService.get_nectar_queryset(nectars_id_list)
        nectars = NectarSerializer(nectars_queryset, many=True)
        WebSocketHelper.send_page_to_user(self.user, "show_nectars", nectars.data)
        return "data has been shown successfully, user is seeing it on his/her screen"

    def get_function_reference(self, function_name: str):
        functions = {
            "show_bees_to_user": self.show_bees_to_user,
            "create_user_profile": create_user,
            "show_hives_to_user": self.show_hives_to_user,
            "show_nectars_to_user": self.show_nectars_to_user
        }
        return functions.get(function_name, lambda **kwargs: print("Function not found"))

    @staticmethod
    def get_or_create_local_thread_by_user(user: User):
        return Thread.objects.get_or_create(user=user)[0]
