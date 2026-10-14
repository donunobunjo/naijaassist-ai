import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY was not found in .env")
    sys.exit(1)

url = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-embedding-001:embedContent"
)

payload = {
    "content": {
        "parts": [
            {
                "text": (
                    "NaijaMobile Hub offers phone buying advice, "
                    "delivery information, warranty support, "
                    "and customer service."
                )
            }
        ]
    },
    "taskType": "RETRIEVAL_DOCUMENT",
    "outputDimensionality": 768,
}

try:
    response = httpx.post(
        url,
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30.0,
    )

    if response.is_error:
        print(f"API request failed with HTTP {response.status_code}.")
        print(response.text[:1000])
        sys.exit(1)

    data = response.json()
    values = data["embedding"]["values"]

    print("SUCCESS: Gemini embedding API is working.")
    print(f"Embedding dimensions: {len(values)}")
    print(f"First five values: {values[:5]}")
    print("The API key has not been displayed.")

except httpx.RequestError as exc:
    print(f"Network error: {type(exc).__name__}: {exc}")
    sys.exit(1)
except (KeyError, TypeError, ValueError) as exc:
    print(f"Unexpected API response: {type(exc).__name__}: {exc}")
    sys.exit(1)