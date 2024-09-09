import inspect
import json
import re
import typing
from typing import Callable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from openai import OpenAI
from openai.types.beta import AssistantResponseFormatParam

from assistant.models import Usage, UserThread
from common.models import Document

User = get_user_model()


class Assistant:
    client = OpenAI(api_key=settings.OPEN_AI_API_KEY)

    def __init__(self, user: User, document_query: QuerySet[Document] or None, instruction: str,
                 functions: [Callable] = None,
                 tread_id=None, format_type: AssistantResponseFormatParam = {"type": "text"},
                 expected_dictionary: typing.Optional[dict] = None,
                 model: typing.Literal[
                     "gpt-4o",
                     "gpt-4o-2024-05-13",
                     "gpt-4-turbo",
                     "gpt-4-turbo-2024-04-09",
                     "gpt-4-0125-preview",
                     "gpt-4-turbo-preview",
                     "gpt-4-1106-preview",
                     "gpt-4-vision-preview",
                     "gpt-4",
                     "gpt-4-0314",
                     "gpt-4-0613",
                     "gpt-4-32k",
                     "gpt-4-32k-0314",
                     "gpt-4-32k-0613",
                     "gpt-3.5-turbo",
                     "gpt-3.5-turbo-16k",
                     "gpt-3.5-turbo-0613",
                     "gpt-3.5-turbo-1106",
                     "gpt-3.5-turbo-0125",
                     "gpt-3.5-turbo-16k-0613",
                 ] = "gpt-4o",
                 ):
        self.user = user
        self.document_query = document_query
        self.instruction = instruction
        self.functions = functions if functions else []
        self.vector_store_id = ""
        self.thread_id = tread_id
        self.format_type = format_type
        self.assistant_id = ""
        self.model = model
        self.json_schema = json.dumps(expected_dictionary) if expected_dictionary else None
        self.__tools = list()
        self.__prepare()

    def send_message(self, message: str, additional_instructions: str = "") -> str or dict:
        self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            content=message,
            role="user"
        )

        if self.format_type["type"] == "json_object":
            self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                content="this json format should be the response: " + self.json_schema,
                role="user"
            )
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                additional_instructions=additional_instructions,
                response_format=self.format_type,
            )
        else:
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                additional_instructions=additional_instructions,
            )

        return self.__process_ai_response(run)

    def __prepare(self):
        if not self.thread_id:
            self.__prepare_files()
            self.__prepare_tools()
            self.__prepare_assistant()
            self.__prepare_thread()

    def __prepare_assistant(self):
        print(self.__tools)
        assistant = self.client.beta.assistants.create(
            instructions=self.instruction,
            name="Talent buzz assistant",
            tools=self.__tools,
            model=self.model,
            tool_resources={"file_search": {"vector_store_ids": [self.vector_store_id]}}
        )
        self.assistant_id = assistant.id

    def __prepare_files(self):
        self.vector_store_id = self.client.beta.vector_stores.create().id
        [self.client.beta.vector_stores.files.create(vector_store_id=self.vector_store_id, file_id=document.file_id) for
         document in self.document_query if document.file_id]

    def __prepare_tools(self):
        tools = [{"type": "file_search"}]
        for func in self.functions:
            func_json = self.__function_to_json(func)
            tools.append({
                "type": "function",
                "function": func_json
            })
        self.__tools = tools

    def __prepare_thread(self):
        self.thread_id = self.client.beta.threads.create(
            metadata={"assistant_id": self.assistant_id, "user_id": str(self.user.id)}
        ).id

        self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            content=self.user.convert_to_ai_readable(),
            role="user"
        )

    def __function_to_json(self, func: Callable):
        exclude_vars = ["user"]
        # Extracting the function's name and docstring
        func_name = func.__name__
        docstring = inspect.getdoc(func)
        docstring = docstring if docstring else ""

        # Analyzing the function's signature
        sig = inspect.signature(func)
        params = sig.parameters

        # Creating the JSON structure for parameters
        parameters_dict = {
            "type": "object",
            "properties": {},
            "required": []
        }

        param_descriptions = self.__parse_docstring(docstring)

        for name, param in params.items():
            if name in exclude_vars:
                continue  # Skip serialization of excluded variables
            # Type hints extraction
            type_hint = typing.get_type_hints(func).get(name, str)  # Default to str if unspecified
            param_type = self.__format_type_hint(type_hint)
            param_description = param_descriptions.get(name, "No description provided.")

            # Parameter properties
            if param_type == "array":
                item_types = [self.__format_type_hint(t) for t in type_hint.__args__]
                parameters_dict["properties"][name] = {
                    "type": param_type,
                    "description": param_description,
                    "items": {"type": item_types[0] if len(item_types) == 1 else item_types}
                }

            else:
                parameters_dict["properties"][name] = {
                    "type": param_type,
                    "description": param_description
                }
            if param.default is param.empty:
                parameters_dict["required"].append(name)

        # Complete JSON structure
        func_json = {
            "name": func_name,
            "description": docstring.split('\n')[0] if docstring else "No detailed description.",
            "parameters": parameters_dict
        }

        return func_json

    def __format_type_hint(self, type_hint):
        if hasattr(type_hint, '__origin__'):
            origin = type_hint.__origin__
            if origin is typing.Union:
                # Assuming Union types are used for Optional fields mostly, which means one type and None
                types = [self.__format_type_hint(t) for t in type_hint.__args__ if t is not type(None)]
                return types[0] if len(types) == 1 else ' | '.join(types)
            elif origin in [list, set, tuple]:
                return "array"
            elif origin is dict:
                key_type, value_type = type_hint.__args__
                return {
                    "type": "object",
                    "properties": {
                        "key": self.__format_type_hint(key_type),
                        "value": self.__format_type_hint(value_type)
                    }
                }
        elif type_hint in [int]:
            return "integer"
        elif type_hint in [float, complex]:
            return "number"
        elif type_hint is type(None):  # Specifically for Optional hints
            return "null"
        elif type_hint is bool:
            return "boolean"
        return "string"  # Default to string if no explicit mapping exists

    @staticmethod
    def __parse_docstring(docstring):
        """
        Parse the docstring to extract parameter descriptions.
        Assumes docstring parameter documentation follows the format:
        :param <name>: <description>
        """
        param_pattern = r":param (\w+): (.+)"
        params = re.findall(param_pattern, docstring)
        return {name: desc.strip() for name, desc in params}

    def __process_ai_response(self, run, retry_count=2):
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
                _function = self.__get_function_reference(tool.function.name)
                try:
                    # print(arguments, self.user)
                    arguments['user'] = self.user
                    print(arguments)
                    function_response = _function(**arguments)
                    print(function_response)
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

            return self.__process_ai_response(
                self.client.beta.threads.runs.submit_tool_outputs_and_poll(tool_outputs=function_responses,
                                                                           run_id=run.id,
                                                                           thread_id=run.thread_id))

        elif run.status == "completed":
            response = self.client.beta.threads.messages.list(thread_id=run.thread_id).data[0]
            if self.format_type['type'] == "json_object":
                try:
                    response_data = json.loads(response.content[0].text.value)
                    # Validate response data with json_schema
                    if not self.__validate_json(response_data):
                        if retry_count > 0:
                            print(f"Schema format is not adhering. Retrying... Remaining retries: {retry_count}")
                            return self.retry_message(retry_count)
                        else:
                            raise ValueError("Failed to get valid JSON response after retries")
                except json.JSONDecodeError:
                    if retry_count > 0:
                        print(f"Validation failed or not JSON. Retrying... Remaining retries: {retry_count}")
                        return self.retry_message(retry_count)
                    else:
                        raise ValueError("Failed to get valid JSON response after retries")
                return response_data
            print(run.usage)
            run_usage = run.usage
            if run_usage:
                Usage.objects.create(
                    user=self.user, model=self.model, type="txt",
                    completion_tokens=run_usage.completion_tokens,
                    prompt_tokens=run_usage.prompt_tokens,
                    run_id=run.id
                )
            return response.content[0].text.value

    def __get_function_reference(self, name: str):
        """Retrieve a function reference from the stored list by function name.

        Args:
            name (str): The name of the function to retrieve.

        Returns:
            Callable: The function object corresponding to the provided name.

        Raises:
            ValueError: If no function with the given name exists in the list.
        """
        for func in self.functions:
            if func.__name__ == name:
                return func
        raise ValueError(f"No function found with the name {name}")

    def __validate_json(self, data):
        # Implement validation logic based on self.json_schema
        schema = json.loads(self.json_schema)
        required_keys = schema.get("required", [])
        for key in required_keys:
            if key not in data:
                return False
        return True

    def retry_message(self, retry_count):
        # Retry the message processing
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id,
        )
        return self.__process_ai_response(run, retry_count - 1)


class AssistantV2:

    def start(self, message: str, user: User):
        data = self.__extract_information_from_threads_based_on_message(user, message)
        self.__get_functions(data, message)
        Assistant(user,document_query=self.__get_files(user, data, message),instruction="").send_message(message)



    def __extract_information_from_threads_based_on_message(self, user: User, message: str) -> str:
        threads = self.__get_user_threads_related_to_message(user, message)
        prompt = self.__generate_prompt_for_data_needed(message)
        data: list = []
        for thread in threads:
            data.append(self.__extract_data_based_on_prompt_on_a_thread(prompt, thread))

        return self.__merge_data(data)

    def __generate_prompt_for_data_needed(self, message: str) -> str:
        return message

    def __merge_data(self, data: typing.List[str]) -> str:
        pass

    def __extract_data_based_on_prompt_on_a_thread(self, prompt: str, thread) -> str:
        pass

    def __get_user_threads_related_to_message(self, user: User, message: str) -> QuerySet[UserThread]:
        threads = self.__get_user_threads(user)
        selected_threads = self.__choose_related_threads(threads, message)
        return selected_threads

    def __choose_related_threads(self, threads, message) -> QuerySet[UserThread]:
        pass

    @staticmethod
    def __get_user_threads(user: User):
        return UserThread.objects.filter(user=user)

    def __select_or_create_thread(self, ) -> UserThread:
        pass


    def __get_functions(self, data: str, message: str):
        pass

    def __get_files(self, user: User, data: str, message: str):
        pass
