import json

from django.conf import settings
from django.contrib.auth import get_user_model
from openai import OpenAI

from honeycomb.honeycomb_service import HiveService, BeeService
from honeycomb.serializers import BeeSerializer
from .helpers import AIBaseClass
from .models import Message, Thread

User = get_user_model()
client = OpenAI(api_key=settings.OPEN_AI_API_KEY)


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
                     ai_type: str = "general_assistant"):

        print (1)
        self.last_message = Message.objects.create(content=message, user=self.user, thread_id=self.local_thread_id)
        hives = self.hive_service.get_user_hives(self.user)
        vector_stores = [self.ai.base_vector_store, ]
        print(1)
        # if ai_type == "hive_assistant":
        #     for hive in hives:
        #         print(hive)
        #         vector_stores.append(self.ai.get_hive_tools(hive.id).get_or_create_hive_vector_store(hive.id))

        thread = self.ai.get_or_create_thread(self.thread_id)
        print(1)
        thread = client.beta.threads.update(
            self.thread_id,
            tool_resources={
                "file_search": {"vector_store_ids": [vector_store.id for vector_store in vector_stores if
                                                     vector_store is not None]}},
            metadata=thread.metadata
        )
        print(1)
        self.ai.add_message_to_thread(thread.id, message)
        print(1)
        run = self.ai.run(self.ai.get_assistant(ai_type).id, thread.id, additional_instructions)
        print(1)
        return self.process_ai_response(run)

    def process_ai_response(self, run):
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
                function_response = _function(**arguments)
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

            response = client.beta.threads.messages.list(thread_id=run.thread_id)[-1]
            self.last_message.response = response.content
            self.last_message.save()
            return response.content

    def show_bees_to_user(self, bees_id_list: [str]) -> str:
        print(bees_id_list)
        bees_queryset = self.bee_service.get_bee_queryset(bees_id_list)
        bees = BeeSerializer(bees_queryset, many=True)
        print(bees.data)
        return "data has been shown successfully"

    def get_function_reference(self, function_name: str):
        functions = {
            "show_bees_to_user": self.show_bees_to_user,
        }
        return functions.get(function_name, lambda **kwargs: print("Function not found"))

    @staticmethod
    def get_or_create_local_thread_by_user(user: User):
        return Thread.objects.get_or_create(user=user)[0]
