from buffer import Buffer
from typing import Dict
import traceback
import tiktoken
import asyncio
import inspect
import openai
import json
import os
import re
openai.api_key = os.getenv('OPENAI_API_KEY')


def gpt_callable(func):
    func.is_gpt_callable = True
    return func

def parse_description(func):
    param_description = {}
    doc = inspect.getdoc(func) or ""
    # matches on the standard docstring style for parameters and their description
    params = re.findall(r":param (.*?): ([\S\s]*)(?=:param|\Z)", doc)  # Modified regex
    
    for param, description in params:
        description = re.sub("\n\s+", " ", description)
        param_description[param] = description.strip()

    return param_description

class Agent:
    def __init__(self):
        self.FUNCTIONS = self._load_callable_functions()
        self.enc = tiktoken.get_encoding('cl100k_base')
        self.func_tokens = len(self.enc.encode(json.dumps(self.FUNCTIONS)))
        self.messages = Buffer()

    def _load_callable_functions(self):
        functions = []
        for func_name, func in inspect.getmembers(self, inspect.ismethod):
            if getattr(func, "is_gpt_callable", False):
                doc = inspect.getdoc(func) or ""
                func_description = re.search(r"^([\s\S]*?)(?=^:param|\Z)", doc, re.MULTILINE).group(1).strip()
                param_description = parse_description(func)
                sig = inspect.signature(func)
                func_info = {
                    'name': func_name,
                    'description': func_description,
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            name: {
                                'type': 'string',
                                'description': param_description.get(name, "No description provided.")
                            }
                            for name in sig.parameters
                        }
                    }
                }
                # Check for required params
                required = [name for name, param in sig.parameters.items()
                            if param.default == inspect.Parameter.empty and
                            param.kind in [
                                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                inspect.Parameter.POSITIONAL_ONLY
                            ]]
                if required:
                    if func_info.get('required'):
                        func_info['required'] += required
                    else:
                        func_info['required'] = required
                functions.append(func_info)
        return functions
    
    async def get_gpt_response(self, prompt: str, primer: str = '') -> str:
        if primer:
            self.messages.append[{'role': 'system', 'content': primer}]

        self.messages.append({'role': 'user', 'content': prompt})

        try:
            response = await openai.ChatCompletion.acreate(
                model='gpt-4',
                messages=self.messages.messages,
                functions=self.FUNCTIONS
            )
            message = response['choices'][0]['message']
            self.messages.append(message)

            if message.get('function_call'):
                return await self.handle_function_call(message)
            else:
                return message['content']


        except Exception as e:
            print(f"Got error: {e}")
            traceback.print_exc()
            return self.messages.messages

    async def handle_function_call(self, message: Dict[str, str]) -> str:
        func_name = message['function_call']['name']
        method_list = [func for func in dir(Agent()) if callable(getattr(Agent(), func))]
        method_list = [func for func in method_list if getattr(getattr(Agent(), func), "is_gpt_callable", False)]
        func = getattr(self, func_name)
        func_args = message['function_call']['arguments']
        
        if isinstance(func_args, str):
            func_args = json.loads(func_args)

        if asyncio.iscoroutinefunction(func):
            result = await func(**func_args)
        else:
            result = func(**func_args)
            
        msg = {'role': 'function', 'name': func_name, 'content': str(result)}
        
        if len(self.enc.encode(str(result))) < 8192 * 0.8:
               self.messages.append(msg)

        second_response = await openai.ChatCompletion.acreate(
            model='gpt-4', 
            messages=self.messages.messages,
            functions=self.FUNCTIONS)   
        second_message = second_response['choices'][0]['message']

        if second_message.get('function_call'):
            return await self.handle_function_call(second_message)
        else:
            self.messages.append(second_message)
            return second_message['content']


    @gpt_callable
    def greet(self, name: str) -> str:
        """
        Generates a simple greeting for the given name
        :param name: Name of person to greet
        """
        return f"Hello, {name}!"

    @gpt_callable
    async def greet_coro(self, name: str) -> str:
        """
        Generates a simple greeting for the given name with a coroutine function
        :param name: Name of person to greet asynchronously
        """
        await asyncio.sleep(0.1)
        return f"Hello, {name}!"
