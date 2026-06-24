from llama_cpp import Llama

model = Llama(
    model_path="models/llama-3-8b-instruct.gguf",
    n_ctx=2048,
    verbose=False,
)

response = model(
    prompt= "用一句话解释什么是 AI agent。",
    max_tokens=128,
    stop=["</s>","\n\n","User:","Assistant:"],
)

"""
choices = response["choices"]
first_choice = choices[0]
text = first_choice["text"]
clean_text = text.strip()

print(clean_text) 

"""

print(response["choices"][0]["text"].strip())