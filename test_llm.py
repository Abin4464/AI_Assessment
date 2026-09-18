import ollama
from config import LLM_MODEL

# ollama.chat send message to local model
response = ollama.chat(
    model=LLM_MODEL,
    messages=[
        {"role": "user", "content": "Reply with exactly one word: Connected"}
    ],
)

# printing the response of the model
print("Model replied:", response["message"]["content"])