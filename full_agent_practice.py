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
            "prompt":prompt,
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

        self.system_prompt = (
            "You are a calm, precise, and helpful "
            "AI assistant."
        )
    

    def simple_generate(self, user_input):
        return self.llm.generate(user_input)
    
    def generate_with_role(self,user_input):
        prompt = f"""{self.system_prompt}

User: {user_input}
Assistant:"""

        return self.llm.generate(prompt)

    def generate_structured (self,user_input,schema):
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
    
    def decide(self,user_input,choices):
        options = "\n".join(
            f"- {choice}"
            for choice in choices
        )

        prompt = f"""{self.system_prompt}

You must choose ONE option from the available choices.
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

    print("Simple result:")
    print(simple_result)

    print("\nRole result:")
    print(role_result)

    print("\nStructured result:")
    print(structured_result)

    print("\nDecision result:")
    print(decision_result)