import openai
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from openai import AssistantEventHandler,OpenAI
from typing_extensions import override

from honeycomb.models import Hive
from honeycomb.serializers import HiveSerializer, NectarSerializer

User = get_user_model()

client = OpenAI(api_key=settings.OPEN_AI_API_KEY)


class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)


def run_message_through_hive_aware_assistant(hive_id: str, message: str, user_id: str, thread_id: str):
    # first we need to create a vector store from documents in the hive, nectars, tasks, reports documents and anything related to the hive
    # then we create an assistant that can search through these documents

    # this is going to be a list of all the documents in the hive searching though all the related models
    file_ids = []
    user = User.objects.get(id=user_id)
    try:
        hive = Hive.objects.get(id=hive_id)
        hive_direct_documents = hive.documents.all()
        for hive_direct_document in hive_direct_documents:
            # Extract the file path from the Document object
            file_path = hive_direct_document.document.path
            with open(file_path, "rb") as file:
                uploaded_file = client.files.create(
                    file=file, purpose="assistants"
                )
                file_ids.append(uploaded_file.id)
        vector_store = client.beta.vector_stores.create(
            name="Product Documentation",
            file_ids=file_ids
        )

        assistant = client.beta.assistants.create(
            name="Talent buzz Hive Assistant",
            instructions="""You are an assistant for helping projects to run smoothly, your job is to make sure you understand the entities and business logic, and then respond to the user prompt properly.
                    the entities are these:
                    user: which represent the human behind the account information
                    bee: which represent freelancer or job provider, in this entity we see job related and experiences related information
                    hive: it is a place that anyone can create or join to others hive, in hive, we have admins (queen bees), members (worker bees), title and description of the hive. a hive a place that queen bee can manage worker bees and worker bees can get job opportunites from their queen bee.
                    
                    nectar: this is the job opportunity itself, nectar is where bees can find some honey (money), for instance, a nectart can be like this, social media marketing, in this entity we have title, description, documents and requirements, and also hourly rate for this job opportunity
                    
                    when the worker bee submit for a nectar and get accepted, their task will be assigned, 
                    each person has one hour to accept the task otherwise it will go to the next avaiable bee, however, when they get accepted in a nectar, it means they are in a contract and they should be avaiable in default.
                    you will be provided with the information you need to know about the hive and nectars in this hive.
                    """,
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            model="gpt-4o",
        )
        if not thread_id:
            thread = client.beta.threads.create()
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"""

                                here are information you need to know:
                                hive data:
                                {HiveSerializer(hive).data}
                                nectars in this hive:
                                {NectarSerializer(hive.nectars.all(), many=True).data}
            """

            )
        else:
            thread = client.beta.threads.retrieve(thread_id)
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=f"Please address the user {user.personal_details.first_name} {user.personal_details.last_name}. The user has a premium account."
        )
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )
            return messages
        else:
            print(run.status)

    except Hive.DoesNotExist:
        raise ValidationError("Hive does not exist")

    except Exception as e:
        raise e
