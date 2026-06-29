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
        self.current_plan = None

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
            "current_plan": self.current_plan,

        }

def create_plan(llm,goal):
    prompt = f"""Create a step-by-step plan to achieve the goal.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{"steps": ["step1", "step2", "step3"]}}

Goal:{goal}

Response (JSON only):"""
    
    for attempt in range(3):
        response = llm.generate(
            prompt,
            temperature=0.0,
        )

        print("raw model response:",response)

        plan = extract_json_from_text(response)

        if(
            plan
            and "steps" in plan
            and isinstance(plan["steps"],list)
        ):
            return plan
        
    return None


class SimpleAgent:
    def __init__(self,model_path):
        self.llm = LocalLLM(model_path)
        self.state = AgentState()

    def create_plan(self,goal):
        plan = create_plan(
            self.llm,
            goal,
        )

        if plan:
            self.state.current_plan = plan

        return plan
    
    def execute_plan(self,plan):
        if not plan or "steps" not in plan:
            return[]
        
        results = []

        for step in plan["steps"]:
            result = {
                "step": step,
                "executed": True,
            }

            results.append(result)
            self.state.increment_step()

        return results
    
agent = SimpleAgent(
        "models/llama-3-8b-instruct.gguf"
)

goal = "Write a blog post about AI agents"

plan = agent.create_plan(goal)

print("Plan:", plan)

if plan:
    results = agent.execute_plan(plan)

    print("Execution results:")

    for index, result in enumerate(results,1):
        print(
            f"Step{index}:",
            result,
        )

print("Agent state:",agent.state.to_dict())