import logging
import httpx
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
    """Verify Meta's signature and reply to incoming WhatsApp text messages."""

    app_secret = settings.meta_app_secret
    access_token = settings.whatsapp_access_token
    phone_number_id = settings.whatsapp_phone_number_id
    api_version = settings.meta_graph_api_version

    if not all([app_secret, access_token, phone_number_id, api_version]):
        raise HTTPException(
            status_code=503,
            detail="WhatsApp integration is not fully configured.",
        )

    # Verify Meta's request signature before trusting the payload.
    signature = request.headers.get("X-Hub-Signature-256", "")
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

    if not hmac.compare_digest(received_signature, expected_signature):
        raise HTTPException(
            status_code=401,
            detail="Webhook signature verification failed.",
        )

    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    # Meta also sends delivery-status notifications, which we don't answer.
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        messages = value.get("messages", [])
    except (KeyError, IndexError, TypeError):
        return {"status": "received", "message": "No incoming messages."}

    if not messages:
        return {"status": "received", "message": "No incoming messages."}

    results = []

    for message in messages:
        # This first version handles text messages only.
        if message.get("type") != "text":
            continue

        sender = message.get("from")
        text = message.get("text", {}).get("body", "").strip()

        if not sender or not text:
            continue

        try:
            # Use the existing pricing service for price-related questions.
            lower_text = text.lower()
            price_keywords = (
                "price", "how much", "cost", "naira", "₦", "sku"
            )

            if any(keyword in lower_text for keyword in price_keywords):
                answer_result = answer_price_question(text)
            else:
                answer_result = answer_question(text)

            # Support either a plain string or a dictionary result.
            if isinstance(answer_result, dict):
                reply = answer_result.get("answer", "")
            else:
                reply = str(answer_result)

            if not reply:
                reply = (
                    "Sorry, I couldn't prepare an answer just now. "
                    "Please try again shortly."
                )

            # WhatsApp text messages have a 4,096-character body limit.
            reply = reply[:4000]

            url = (
                f"https://graph.facebook.com/"
                f"{api_version}/{phone_number_id}/messages"
            )

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            outgoing_message = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": sender,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": reply,
                },
            }

            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=outgoing_message,
                )

            if response.is_success:
                results.append({"status": "sent"})
            else:
                # Avoid logging tokens or the customer's message.
                print(
                    "WhatsApp send failed:",
                    response.status_code,
                    response.text[:500],
                )
                results.append({"status": "send_failed"})

        except Exception as exc:
            # Keep diagnostics limited; never log secrets or message contents.
            print("WhatsApp message processing failed:", type(exc).__name__)
            results.append({"status": "processing_failed"})

    return {"status": "processed", "results": results}
