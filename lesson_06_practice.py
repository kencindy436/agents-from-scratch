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
    
class SimpleAgent:
    def __init__(self,model_path):
        self.llm = LocalLLM(model_path)
        self.system_prompt = "You are a calm, precise, and helpful AI assistant."
        self.state = AgentState()

    def agent_step(self,user_input):
        state_dict = self.state.to_dict()

        prompt = f"""{self.system_prompt}

You are an agent. You must decide the next action and respond with ONLY valid JSON.

Current state: steps={state_dict.get("steps",0)}, done={state_dict.get("done",False)}

Available actions: analyze, research, summarize, answer, done

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{"action": "action_name", "reason": "explanation"}}

User input: {user_input}

Response (JSON only):"""
        
        for attempt in range(3):
            response = self.llm.generate(prompt,temperature=0.0)
            print("Raw model response:",response)

            parsed = extract_json_from_text(response)

            if parsed and "action" in parsed:
                if "reason" not in parsed:
                    parsed["reason"] = f"Taking action: {parsed['action']}"

                self.state.increment_step()
                return parsed
        return None
    
    def run_loop(self,user_input,max_steps=5):
        self.state.reset()
        results = []

        while not self.state.done and self.state.steps < max_steps:
            action = self.agent_step(user_input)

            if action:
                results.append(action)

                if action.get("actions") == "done":
                    self.state.mark_done()
            
            else:
                break

        return results

agent = SimpleAgent("models/llama-3-8b-instruct.gguf")

results = agent.run_loop("Help me understand loops", max_steps=3)

for i, result in enumerate(results, 1):
    print(f"Iteration {i}:")
    action = result.get("action", "unknown")
    reason = result.get("reason", "No reason provided")
    print(f"  Action: {action}")
    print(f"  Reason: {reason}")

    if i < len(results):
        print()  