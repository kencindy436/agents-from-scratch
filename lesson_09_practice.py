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

def generate_plan(llm,goal):
    prompt = f"""Create a step-by-step plan to achieve the goal.

   CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{"steps": ["step1", "step2", "step3"]}}

Goal:
{goal}

Response (JSON only):"""

    for attempt in range(3):
        response = llm.generate(
            prompt,
            temperature=0.0,
        )

        print("raw plan response:",response)

        plan = extract_json_from_text(response)

        if (
            plan
            and "steps" in plan
            and isinstance(plan["steps"],list)
        ):
            return plan
    
    return None

def generate_atomic_action(llm,step):
    prompt = f"""Convert this step into an atomic action.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{
  "action": "action_name",
  "inputs": {{"key": "value"}}
}}

The action should be a simple, atomic operation name.
The inputs should contain the parameters needed for the action.

Step to convert:
{step}

Response (JSON only):"""
    
    for attempt in range(3):
        response = llm.generate(
            prompt,
            temperature=0.0,
        )

        print("raw atomic action response:",response)

        action = extract_json_from_text(response)

        if(
            action
            and "action" in action
            and "inputs" in action
            and isinstance(action["inputs"],dict)
        ):
            return action
    return None

class SimpleAgent:
    def __init__(self,model_path):
        self.llm = LocalLLM(model_path)

    def create_plan(self,goal):
        return generate_plan(
            self.llm,
            goal,

        )
    
    def create_atomic_action(self,step):
        return generate_atomic_action(
            self.llm,
            step,

        )
    
agent = SimpleAgent(
    "models/llama-3-8b-instruct.gguf"
)

goal = "Create a tutorial about Python"

# 第一次调用模型：根据目标生成计划
plan = agent.create_plan(goal)

print("Plan:", plan)

if plan and plan["steps"]:
    # Python 从整个计划中取出第一步
    first_step = plan["steps"][0]

    print("First step:", first_step)

    # 第二次调用模型：把第一步转换成原子动作
    atomic_action = agent.create_atomic_action(first_step)

    print("Atomic action:", atomic_action)
else:
    print("Plan generation failed.")
