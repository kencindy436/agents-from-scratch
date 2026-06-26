import json
from typing import Any
from llama_cpp import Llama

def  extract_json_from_text(text):
    start = text.find("{")


    if start == -1 :
        return None
    
    decoder = json.JSONDecoder()

    try:
        parsed, end = decoder.raw_decode(text[start:])
        return parsed
    except json.JSONDecodeError:
        return None
    

class LocalLLM:
    def __init__(self, model_path):
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            verbose=False,
        )

    def generate(self, prompt,temperature=None):
        kwargs = {
            "prompt":prompt,
            "max_tokens":128,
            "stop":["</s>", "\n\n", "User:", "Assistant:"],
        }

        if temperature is not None:
            kwargs["temperature"] = temperature

        response = self.llm(**kwargs)
        return response["choices"][0]["text"].strip()

def calculator(a:float,b:float,operation:str = "add") -> float:
    operations = {
        "add": lambda x,y: x + y,
        "substract": lambda x,y: x - y,
        "multiply": lambda x,y: x * y,
        "divide": lambda x,y: x/y if y != 0 else float("inf"),
    }

    if operation not in operations:
        raise ValueError(f"Unknown operation:{operation}")
    
    return operations[operation](a,b)

def  execute_tool(tool_name:str,arguments:dict) -> Any:
    tools = {
        "calculator":calculator,
    }

    if tool_name not in tools:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    return tools[tool_name](**arguments)


class SimpleAgent:
    def __init__(self, model_path):
        self.llm = LocalLLM(model_path)
        self.system_prompt = "You are a helpful AI assistant."

    def request_tool(self,user_input):
        prompt = f"""{self.system_prompt}

You are a tool-calling assistant. When asked a math question, you must respond with ONLY valid JSON.

Available tool: calculator
- Parameters: a (number), b (number), operation ("add", "subtract", "multiply", or "divide")

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Example format:
{{"tool": "calculator", "arguments": {{"a": 42, "b": 7, "operation": "multiply"}}}}

User request: {user_input}

Response (Json only):"""
        
        for attempt in range(3):
            response = self.llm.generate(prompt,temperature=0.0)
            print("Raw model response:",response)

            parsed = extract_json_from_text(response)

            if parsed and "tool" in parsed and "arguments" in parsed:
                return parsed
        
        return None
    
    def execute_tool_call(self,tool_call):
        return execute_tool(tool_call["tool"],tool_call["arguments"])
    
agent = SimpleAgent("models/llama-3-8b-instruct.gguf")

tool_call = agent.request_tool("What is 42 * 7?")
print("Tool request:",tool_call)

if tool_call:
    result = agent.execute_tool_call(tool_call)
    print("Tool result:",result)