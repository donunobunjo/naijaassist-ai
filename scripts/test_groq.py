import os

from dotenv import load_dotenv
from groq import Groq

# Load environment variables.
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY is missing. Check your .env file."
    )

client = Groq(api_key=api_key)

# Model returned by your Groq account.
MODEL = "qwen/qwen3.8-27b"

print(f"Testing NaijaAssist AI with {MODEL}...")

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are NaijaAssist AI, a helpful customer-service "
                    "assistant for NaijaMobile Hub, a Nigerian mobile "
                    "phone retailer. Be polite and concise. Never invent "
                    "product prices, stock availability, or company policies."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Good afternoon. My budget is ₦250,000, and I want "
                    "to buy a Samsung smartphone. Can you help me?"
                ),
            },
        ],
        max_completion_tokens=150,
    )

    answer = response.choices[0].message.content

    print("\nNaijaAssist AI response:")
    print(answer or "(The model returned an empty response.)")

    print("\nUsage:")
    print(response.usage)

except Exception as error:
    print("\nInference test failed.")
    print(f"Error type: {type(error).__name__}")
    print(f"Details: {error}")