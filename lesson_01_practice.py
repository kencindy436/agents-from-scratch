
#llm打包成agent

from llama_cpp import Llama

class SimpleAgent:
    def __init__(self,model_path):
        self.model = Llama (
            model_path=model_path,
            n_ctx=2048,
            verbose=False,
        )
    def simple_generate(self,user_input):
        response = self.model(
            prompt=user_input,
            max_tokens=128,
            stop=["</s>", "\n\n", "User:", "Assistant:"],
        )

        return response["choices"][0]["text"].strip()

agent = SimpleAgent("models/llama-3-8b-instruct.gguf")
response = agent.simple_generate("Explain what an AI agent is in one sentence.")

print(response)
