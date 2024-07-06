import inspect
import json
import re
import typing
from typing import Callable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from openai import OpenAI

from common.models import Document

User = get_user_model()


class Assistant:
    client = OpenAI(api_key=settings.OPEN_AI_API_KEY)

    def __init__(self, user: User, document_query: QuerySet[Document], instruction: str, functions: [Callable],
                 tread_id=None):
        self.user = user
        self.document_query = document_query
        self.instruction = instruction
        self.functions = functions
        self.vector_store_id = ""
        self.thread_id = tread_id
        self.assistant_id = ""
        self.__tools = list()
        self.__prepare()

    def send_message(self, message: str, additional_instructions: str = ""):
        self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            content=message,
            role="user"
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id,
            additional_instructions=additional_instructions
        )
        return self.__process_ai_response(run)

    def __prepare(self):
        if not self.thread_id:
            self.__prepare_files()
            self.__prepare_tools()
            self.__prepare_assistant()
            self.__prepare_thread()

    def __prepare_assistant(self):
        assistant = self.client.beta.assistants.create(
            instructions=self.instruction,
            name="Math Tutor",
            tools=self.__tools,
            model="gpt-4o",
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
            metadata={"assistant_id": self.assistant_id, "user_id": self.user.id}
        ).id

        self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            content=User.convert_to_ai_readable(),
            role="user"
        )

    def __function_to_json(self, func: Callable):
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
            # Type hints extraction
            type_hint = typing.get_type_hints(func).get(name, str)  # Default to str if unspecified
            param_type = self.__format_type_hint(type_hint)
            param_description = param_descriptions.get(name, "No description provided.")

            # Parameter properties
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
                item_types = [self.__format_type_hint(t) for t in type_hint.__args__]
                return {
                    "type": "array",
                    "items": item_types[0] if len(item_types) == 1 else item_types
                }
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

    def __process_ai_response(self, run):
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
                    function_response = _function(**arguments, user=self.user)
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
