
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_EMBEDDING_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-embedding-001:embedContent"
)

EMBEDDING_DIMENSIONS = 768


def embed_text(
    text: str,
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[float]:
    """Generate a 768-dimensional embedding using Gemini."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from the environment.")

    if not text or not text.strip():
        raise ValueError("Cannot embed empty text.")

    payload = {
        "content": {
            "parts": [{"text": text}]
        },
        "taskType": task_type,
        "outputDimensionality": EMBEDDING_DIMENSIONS,
    }

    response = httpx.post(
        GEMINI_EMBEDDING_URL,
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30.0,
    )
    response.raise_for_status()

    result = response.json()
    vector = result["embedding"]["values"]

    if len(vector) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
            f"received {len(vector)}."
        )

    return vector
