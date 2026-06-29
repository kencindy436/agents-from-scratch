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

class AgentState:
    def __init__(self):
        self.steps = 0
        self.done = False

    def increment_step(self):
        self.steps = self.steps + 1

    def mark_done(self):
        self.done = True

    def reset(self):
        self.steps = 0 
        self.done = False

    def to_dict(self):
        return {
            "steps":self.steps,
            "done":self.done,

        }

class Memory:
    def __init__(self):
        self.items = []

    def  add(self,item):
        if item and item not in self.items:
            self.items.append(item)

    def get_all(self):
        return self.items.copy()
    
    def clear(self):
        self.items = []


    
class SimpleAgent:
    def __init__(self,model_path):
        self.llm = LocalLLM(model_path)
        self.system_prompt = "You are a calm, precise, and helpful AI assistant."
        self.state = AgentState()
        self.memory = Memory()

    def run_with_memory(self,user_input):
        memory_context = self.memory.get_all()

        if memory_context:
            memory_str = (
                "you remember the following:\n"
                + "\n".join(
                    f"- {item}" for item in memory_context
                )
            )
        else:
            memory_str = "you have no memories yet."

        prompt = f"""{self.system_prompt}

You are an agent with memory.
You must respond with ONLY valid JSON.

{memory_str}

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}
4. If the user tells you information, save it to memory
5. If the user asks about something you remember, use your memory

Required JSON format:
{{"reply": "your response text", "save_to_memory": "fact to remember" or null}}

Examples:
- User says "My name is Alice"
  -> {{"reply": "Nice to meet you, Alice!", "save_to_memory": "User's name is Alice"}}

- User asks "What's my name?"
  -> {{"reply": "Your name is Alice", "save_to_memory": null}}

User input:{user_input}

Response (JSON only)):"""
        for attempt in range(3):
            response = self.llm.generate(
                prompt,
                temperature=0.0
            )
        
            print("raw model response:", response)

            parsed = extract_json_from_text(response)

            if parsed and "reply" in parsed:
                memory_item = parsed.get("save_to_memory")

                if memory_item:
                    self.memory.add(memory_item)

                self.state.increment_step()
                return parsed
        return None
    
agent = SimpleAgent("models/llama-3-8b-instruct.gguf")

response1 = agent.run_with_memory(
    "my name is alice"
)

if response1 and "reply" in response1:
    print("Response 1:", response1["reply"])

    if response1.get("save_to_memory"):
        print(
            "Save to memory:",
            response1["save_to_memory"],
        )

else:
    print("Response 1:",response1)

response2 = agent.run_with_memory(
    "What's my name?"
)

if response2 and "reply" in response2:
    print("Response 2:", response2["reply"])
else:
    print("Response 2:", response2) 
            
print("Memory contents:", agent.memory.get_all())
print("Agent steps:", agent.state.steps)  
    

