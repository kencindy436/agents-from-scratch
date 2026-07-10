import json

from llama_cpp import Llama


def extract_json_from_text(text):
    start = text.find("{")

    if start == -1:
        return None

    decoder = json.JSONDecoder()

    try:
        parsed, _ = decoder.raw_decode(text[start:])
        return parsed
    except json.JSONDecodeError:
        return None


def calculator(a, b, operation="add"):
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else float("inf"),
    }

    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")

    return operations[operation](a, b)


def execute_tool(tool_name, arguments):
    tools = {
        "calculator": calculator,
    }

    if tool_name not in tools:
        raise ValueError(f"Unknown tool: {tool_name}")

    return tools[tool_name](**arguments)


class AgentState:
    def __init__(self):
        self.steps = 0
        self.done = False
        self.last_action = None

    def increment_step(self):
        self.steps += 1

    def mark_done(self):
        self.done = True

    def reset(self):
        self.steps = 0
        self.done = False
        self.last_action = None

    def to_dict(self):
        return {
            "steps": self.steps,
            "done": self.done,
            "last_action": self.last_action,
        }


class LocalLLM:
    def __init__(
        self,
        model_path,
        temperature=0.2,
        max_tokens=512,
        n_ctx=2048,
    ):
        self.llm = Llama(
            model_path=model_path,
            temperature=temperature,
            n_ctx=n_ctx,
            verbose=False,
        )

        self.max_tokens = max_tokens

    def generate(
        self,
        prompt,
        temperature=None,
        stop=None,
    ):
        kwargs = {
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "stop": (
                stop
                if stop is not None
                else [
                    "</s>",
                    "\n\n",
                    "User:",
                    "Assistant:",
                ]
            ),
        }

        if temperature is not None:
            kwargs["temperature"] = temperature

        response = self.llm(**kwargs)

        return (
            response["choices"][0]["text"]
            .strip()
        )


class SimpleAgent:
    def __init__(self, model_path):
        self.llm = LocalLLM(model_path)
        self.state = AgentState()

        self.system_prompt = (
            "You are a calm, precise, and helpful "
            "AI assistant."
        )

    def simple_generate(self, user_input):
        return self.llm.generate(user_input)

    def generate_with_role(self, user_input):
        prompt = f"""{self.system_prompt}

User: {user_input}
Assistant:"""

        return self.llm.generate(prompt)

    def generate_structured(self, user_input, schema):
        prompt = f"""{self.system_prompt}

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no extra text before or after the JSON
3. Start your response with {{ and end with }}

Schema you must follow:
{schema}

User request: {user_input}

Response (JSON only):"""

        for _ in range(3):
            response = self.llm.generate(
                prompt,
                temperature=0.0,
                stop=["</s>", "User:", "Assistant:"],
            )
            parsed = extract_json_from_text(response)

            if isinstance(parsed, dict):
                return parsed

        return None

    def decide(self, user_input, choices):
        options = "\n".join(
            f"- {choice}"
            for choice in choices
        )

        prompt = f"""{self.system_prompt}

You must choose ONE option from the available choices.
Choose "use_tool" for arithmetic, calculation, or math questions.
Choose "answer_question" for explanations, definitions, or general knowledge questions.
Respond with ONLY valid JSON.

Available choices:
{options}

Required JSON format:
{{"decision": "one_of_the_choices_above"}}

User request: {user_input}

Response (JSON only):"""

        for _ in range(3):
            response = self.llm.generate(
                prompt,
                temperature=0.0,
                stop=["</s>", "User:", "Assistant:"],
            )
            parsed = extract_json_from_text(response)

            if (
                isinstance(parsed, dict)
                and "decision" in parsed
                and parsed["decision"] in choices
            ):
                return parsed["decision"]

        return None

    def request_tool(self, user_input):
        prompt = f"""{self.system_prompt}

You are a tool-calling assistant. When a user asks a math question,
respond with ONLY valid JSON that requests the correct tool.

Available tool:
calculator
- arguments:
  - a: number
  - b: number
  - operation: "add" | "subtract" | "multiply" | "divide"

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Example format:
{{"tool": "calculator", "arguments": {{"a": 42, "b": 7, "operation": "multiply"}}}}

User request: {user_input}

Response (JSON only):"""

        for _ in range(3):
            response = self.llm.generate(
                prompt,
                temperature=0.0,
                stop=["</s>", "User:", "Assistant:"],
            )
            parsed = extract_json_from_text(response)

            if (
                isinstance(parsed, dict)
                and parsed.get("tool") == "calculator"
                and isinstance(parsed.get("arguments"), dict)
            ):
                return parsed

        return None

    def execute_tool_call(self, tool_call):
        return execute_tool(
            tool_call["tool"],
            tool_call["arguments"],
        )

    def agent_step(self, user_input):
        allowed_actions = [
            "analyze",
            "research",
            "summarize",
            "answer",
            "done",
        ]
        state_dict = self.state.to_dict()

        prompt = f"""{self.system_prompt}

You are an agent. Decide the next action based on the user input and current state.
Respond with ONLY valid JSON.

Current state:
- steps: {state_dict.get("steps", 0)}
- done: {state_dict.get("done", False)}
- last_action: {state_dict.get("last_action")}

Available actions:
- analyze
- research
- summarize
- answer
- done

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{"action": "action_name", "reason": "explanation"}}

User input: {user_input}

Response (JSON only):"""

        for _ in range(3):
            response = self.llm.generate(
                prompt,
                temperature=0.0,
                stop=["</s>", "User:", "Assistant:"],
            )
            parsed = extract_json_from_text(response)

            if (
                isinstance(parsed, dict)
                and parsed.get("action") in allowed_actions
            ):
                if "reason" not in parsed:
                    parsed["reason"] = (
                        f"Taking action: {parsed['action']}"
                    )

                self.state.last_action = parsed
                self.state.increment_step()
                return parsed

        return None

    def run_loop(self, user_input, max_steps=5):
        self.state.reset()
        results = []

        while (
            not self.state.done
            and self.state.steps < max_steps
        ):
            action = self.agent_step(user_input)

            if action is None:
                break

            results.append(action)

            if action.get("action") == "done":
                self.state.mark_done()

        return results

    def run(self, user_input):
        decision = self.decide(
            user_input,
            [
                "answer_question",
                "use_tool",
            ],
        )

        if decision == "use_tool":
            tool_call = self.request_tool(user_input)

            if tool_call is None:
                return {
                    "type": "error",
                    "decision": decision,
                    "message": "Could not create a valid tool call.",
                }

            tool_result = self.execute_tool_call(tool_call)

            return {
                "type": "tool_result",
                "decision": decision,
                "tool_call": tool_call,
                "result": tool_result,
            }

        if decision == "answer_question":
            answer = self.generate_with_role(user_input)

            return {
                "type": "answer",
                "decision": decision,
                "result": answer,
            }

        return {
            "type": "error",
            "decision": decision,
            "message": "Could not decide which action to take.",
        }


if __name__ == "__main__":
    agent = SimpleAgent(
        "models/llama-3-8b-instruct.gguf"
    )

    assert extract_json_from_text(
        'before {"ok": true} after'
    ) == {"ok": True}

    simple_result = agent.simple_generate(
        "Explain what an AI agent is "
        "in one sentence."
    )

    assert isinstance(simple_result, str)
    assert simple_result

    role_result = agent.generate_with_role(
        "Explain what an AI agent is "
        "in one sentence."
    )

    assert isinstance(role_result, str)
    assert role_result

    schema = """
{
  "topic": "string",
  "difficulty": "beginner | intermediate | advanced"
}
"""

    structured_result = agent.generate_structured(
        "Classify this lesson: Python variables for beginners.",
        schema,
    )

    assert isinstance(structured_result, dict)
    assert "topic" in structured_result
    assert "difficulty" in structured_result

    decision_result = agent.decide(
        "Translate hello to Spanish.",
        [
            "answer_question",
            "summarize_text",
            "translate",
        ],
    )

    assert decision_result == "translate"

    fixed_tool_call = {
        "tool": "calculator",
        "arguments": {
            "a": 42,
            "b": 7,
            "operation": "multiply",
        },
    }

    fixed_tool_result = agent.execute_tool_call(fixed_tool_call)

    assert fixed_tool_result == 294

    tool_call = agent.request_tool("What is 42 * 7?")

    assert isinstance(tool_call, dict)
    assert tool_call["tool"] == "calculator"
    assert isinstance(tool_call["arguments"], dict)

    tool_result = agent.execute_tool_call(tool_call)

    assert tool_result == 294

    math_run_result = agent.run("What is 42 * 7?")

    assert isinstance(math_run_result, dict)
    assert math_run_result["type"] == "tool_result"
    assert math_run_result["decision"] == "use_tool"
    assert math_run_result["result"] == 294

    loop_results = agent.run_loop(
        "Help me understand agent loops.",
        max_steps=3,
    )

    allowed_loop_actions = {
        "analyze",
        "research",
        "summarize",
        "answer",
        "done",
    }

    assert isinstance(loop_results, list)
    assert loop_results
    assert len(loop_results) <= 3
    assert all(
        isinstance(result, dict)
        and result.get("action") in allowed_loop_actions
        for result in loop_results
    )
    assert agent.state.steps == len(loop_results)

    print("Simple result:")
    print(simple_result)

    print("\nRole result:")
    print(role_result)

    print("\nStructured result:")
    print(structured_result)

    print("\nDecision result:")
    print(decision_result)

    print("\nFixed tool result:")
    print(fixed_tool_result)

    print("\nTool request:")
    print(tool_call)

    print("\nTool result:")
    print(tool_result)

    print("\nRun result:")
    print(math_run_result)

    print("\nAgent loop results:")

    for index, result in enumerate(loop_results, 1):
        print(f"Iteration {index}:")
        print(f"  Action: {result.get('action')}")
        print(f"  Reason: {result.get('reason')}")

    print("\nFinal agent state:")
    print(agent.state.to_dict())
