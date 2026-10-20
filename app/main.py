
import hashlib
import hmac
import re

import psycopg
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.services.products import search_products as lookup_products
from app.services.rag import answer_question
from app.services.price_answer import answer_price_question


app = FastAPI(
    title="NaijaAssist AI",
    description=(
        "AI-powered customer service API for a fictional "
        "Nigerian mobile phone retailer."
    ),
    version="1.0.0",
)


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The customer's question.",
    )


@app.get("/", tags=["General"])
def root():
    """Return basic API information."""
    return {
        "service": "NaijaAssist AI",
        "message": "Welcome to the NaijaAssist AI API.",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["General"])
def health_check():
    """Check whether the application and database are available."""
    try:
        with psycopg.connect(
            settings.database_url,
            connect_timeout=5,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()

        return {
            "status": "healthy",
            "service": "NaijaAssist AI",
            "database": "connected",
        }

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="The database is currently unavailable.",
        ) from None


@app.get("/products", tags=["Products"])
def get_products(
    search: str = Query(
        ...,
        min_length=1,
        max_length=200,
        description="Search by phone model, brand, or product name.",
    ),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Search the product catalogue."""
    try:
        return lookup_products(
            search=search.strip(),
            limit=limit,
        )

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="Product information is temporarily unavailable.",
        ) from None


@app.post("/chat", tags=["AI Customer Service"])
def chat(request: ChatRequest):
    """
    Answer customer questions using verified pricing or RAG.

    Price questions use the pricing service. Other questions
    use retrieval-augmented generation over the knowledge base.
    """
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Please enter a question.",
        )

    # Detect common price-related questions.
    price_keywords = (
        "price",
        "how much",
        "cost",
        "naira",
        "\u20a6",
        "sku",
    )

    is_price_question = any(
        keyword in question.lower()
        for keyword in price_keywords
    )

    try:
        if is_price_question:
            # Remove common price-question wording so the product
            # search receives a cleaner product name or SKU.
            product_query = re.sub(
                r"^\s*(?:how much is|what is the price of|"
                r"what's the price of|what is the cost of|"
                r"price of|cost of)\s+",
                "",
                question,
                flags=re.IGNORECASE,
            ).strip().rstrip("?!., ")

            answer = answer_price_question(product_query)

            return {
                "service": "NaijaAssist AI",
                "question": question,
                "answer": answer,
                "sources": [
                    {
                        "title": "Product Catalogue and Verified Pricing",
                        "source_path": (
                            "database: products and product_prices"
                        ),
                    }
                ],
                "data_notice": (
                    "Catalogue and pricing data are synthetic "
                    "demonstration data, not real retailer offers. "
                    "Availability is not confirmed through a live "
                    "retailer inventory system."
                ),
            }

        # Non-price questions use the RAG pipeline.
        result = answer_question(question)

        return {
            "service": "NaijaAssist AI",
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
            "data_notice": (
                "NaijaMobile Hub policies and catalogue data are "
                "fictional demonstration data."
            ),
        }

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Customer service information is temporarily "
                "unavailable. Please try again shortly."
            ),
        ) from None

    except Exception:
        # Keep internal errors and configuration details out of
        # customer-facing API responses.
        raise HTTPException(
            status_code=502,
            detail=(
                "We could not complete your request right now. "
                "Please try again shortly."
            ),
        ) from None


@app.get(
    "/webhook/whatsapp",
    tags=["WhatsApp"],
    response_class=PlainTextResponse,
)
def verify_whatsapp_webhook(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(
        default="",
        alias="hub.verify_token",
    ),
    hub_challenge: str = Query(
        default="",
        alias="hub.challenge",
    ),
):
    """
    Handle Meta's WhatsApp webhook verification request.
    """
    expected_token = settings.whatsapp_verify_token

    if (
        hub_mode == "subscribe"
        and expected_token
        and hmac.compare_digest(
            hub_verify_token,
            expected_token,
        )
    ):
        return hub_challenge

    raise HTTPException(
        status_code=403,
        detail="WhatsApp webhook verification failed.",
    )


@app.post("/webhook/whatsapp", tags=["WhatsApp"])
async def receive_whatsapp_webhook(request: Request):
    """
    Receive WhatsApp webhook events.

    Message processing remains disabled until Meta signature
    verification and safe message handling are implemented.
    """
    app_secret = settings.meta_app_secret

    if not app_secret:
        raise HTTPException(
            status_code=503,
            detail=(
                "WhatsApp webhook processing is not configured."
            ),
        )

    signature = request.headers.get(
        "X-Hub-Signature-256",
        "",
    )

    if not signature.startswith("sha256="):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid webhook signature.",
        )

    raw_body = await request.body()

    expected_signature = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    received_signature = signature.removeprefix("sha256=")

    if not hmac.compare_digest(
        received_signature,
        expected_signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Webhook signature verification failed.",
        )

    # Signature verification is implemented, but inbound message
    # processing and replies have not yet been connected.
    raise HTTPException(
        status_code=501,
        detail=(
            "Webhook signature verified, but WhatsApp message "
            "processing has not been implemented yet."
        ),
    )
