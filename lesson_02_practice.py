from llama_cpp import Llama


class LocalLLM:
    def __init__(self, model_path):
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            verbose=False,
        )

    def generate(self, prompt):
        response = self.llm(
            prompt=prompt,
            max_tokens=128,
            stop=["</s>", "\n\n", "User:", "Assistant:"],
        )

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
Assitant:"""

        response = self.llm.generate(prompt)
        return response.strip()

agent = SimpleAgent("models/llama-3-8b-instruct.gguf")
response = agent.generate_with_role("Explain what an AI agent is in one sentence.")
print(response)