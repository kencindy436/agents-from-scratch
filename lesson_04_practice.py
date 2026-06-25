import json
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


class SimpleAgent:
    def __init__(self, model_path):
        self.llm = LocalLLM(model_path)
        self.system_prompt = (
            "你是一个中文 AI 教学助手。"
            "你只使用中文回答。"
            "你用简单、清楚的语言解释概念。"
            "不要提供英文翻译。" 
        )
    def simple_generate(self, user_input):
        return self.llm.generate(user_input)

    def generate_with_role(self,user_input):
        prompt = f"""{self.system_prompt}
    
User: {user_input}
Assistant:"""

        response = self.llm.generate(prompt)
        return response.strip()
    
    def generate_structured(self,user_input,schema):
        prompt = f"""{self.system_prompt}

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no extra text before or after the JSON
3. Start your response with {{ and end with }}

Schema you must follow:
{schema}

User request: {user_input}

Response (Json only):"""
        
        for attempt in range(3):
            response = self.llm.generate(prompt,temperature=0.0)
            parsed = extract_json_from_text(response)

            if parsed is not None:
                return parsed
            
        return None

    def decide(self,user_input,choices):
        options = "\n".join(f"- {choice}" for choice in choices)

        prompt = f"""{self.system_prompt}

You must choose ONE of the following options. Respond with ONLY valid JSON.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Available choices:
{options}

Required JSON format:
{{"decision":"one_of_the_choices_above"}}

User request: {user_input}

Response (JSON only):"""
        for attempt in range(3):
            response = self.llm.generate(prompt,temperature=0.0)
            parsed = extract_json_from_text(response)

            if parsed and "decision" in parsed:
                decison = parsed["decision"]

                if decison in choices:
                    return decison
        
        return None
    

agent = SimpleAgent("models/llama-3-8b-instruct.gguf")

decision = agent.decide(
    "can you summarize this article for me",
    choices=["answer_question","summarize_text","translate"]
)

print(decision)