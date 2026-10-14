import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables from the project .env file.
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN is missing. Check your project's .env file."
    )

# Let Hugging Face select a compatible inference provider.
client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN,
)

MODEL = "Qwen/Qwen2.5-3B-Instruct"

print(f"Testing hosted inference with {MODEL}...")

try:
    response = client.chat_completion(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are NaijaAssist AI, a polite customer service "
                    "assistant for a Nigerian mobile phone retailer."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Greet a Nigerian customer who wants to buy a "
                    "smartphone. Use no more than two sentences."
                ),
            },
        ],
        max_tokens=100,
    )

    print("\nModel response:")
    print(response.choices[0].message.content)

except Exception as error:
    print("\nInference test failed.")
    print(f"Error type: {type(error).__name__}")
    print(f"Details: {error}")