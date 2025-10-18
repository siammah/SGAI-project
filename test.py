from groq import Groq
import os

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)
try:
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": "Say hello!"}],
        max_completion_tokens=32,
        stream=False,
    )
    print(completion)
except Exception as e:
    print("Groq error:", e)