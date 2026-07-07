from llama_cpp import Llama


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

        self.system_prompt = (
            "You are a calm, precise, and helpful "
            "AI assistant."
        )

    def simple_generate(self, user_input):
        return self.llm.generate(user_input)


if __name__ == "__main__":
    agent = SimpleAgent(
        "models/llama-3-8b-instruct.gguf"
    )

    result = agent.simple_generate(
        "Explain what an AI agent is "
        "in one sentence."
    )

    assert isinstance(result, str)
    assert result

    print("Model result:")
    print(result)