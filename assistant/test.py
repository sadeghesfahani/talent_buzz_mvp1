import inspect
import json
import re
import typing
from typing import Callable


class Assistant:

    def __init__(self, functions: [Callable]):
        self.functions = functions
        self.__prepare()


    def __prepare(self):
        function_array_json = []
        for func in self.functions:
            function_array_json.append(self.__function_to_json(func))

        print(function_array_json)


        # 1. create a vector sector out of the document query
        # 2. create a thread for the user
        # 3. add user information to the thread
        # 4. add the vector sector to the thread
        # 5. add the instruction to the thread
        # 6. add the functions to the thread

        pass
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


def some_function(a: int, b: str="sina", c: bool = True) -> str:
    """
    This is a test function
    :param a: this is going to be something greate
    :param b:
    :param c:
    :return:
    """
    pass

def somefunction2(a: typing.List[str], b: typing.List[int]) -> str:
    pass


assistant = Assistant([some_function, somefunction2])