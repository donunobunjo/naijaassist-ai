
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
import psycopg

from app.config import settings
from app.services.products import search_products as lookup_products


app = FastAPI(
    title="NaijaAssist AI",
    description=(
        "AI-powered customer service API for NaijaMobile Hub. "
        "Product catalogue data is synthetic demonstration data."
    ),
    version="0.1.0",
)


# --------------------------------------------------
# 1. Health Check
# --------------------------------------------------

@app.get("/health", tags=["System"])
def health_check():
    """Confirm that the API application is running."""
    return {
        "status": "healthy",
        "service": "NaijaAssist AI",
        "version": "0.1.0",
    }


# --------------------------------------------------
# 2. Product Catalogue Search
# --------------------------------------------------

@app.get("/products", tags=["Products"])
def get_products(
    search: str = Query(
        ...,
        min_length=1,
        max_length=100,
        description="Search by product name, brand, SKU, or description.",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of products to return.",
    ),
):
    """
    Search the product catalogue.

    Price verification and database queries are handled
    by the product service layer.
    """
    if not search.strip():
        raise HTTPException(
            status_code=422,
            detail="Please provide a product name, brand, or SKU.",
        )

    try:
        return lookup_products(
            search=search.strip(),
            limit=limit,
        )
    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail=(
                "The product catalogue is temporarily unavailable. "
                "Please try again later."
            ),
        ) from None


# --------------------------------------------------
# 3. WhatsApp Webhook Verification
# --------------------------------------------------

@app.get(
    "/webhook/whatsapp",
    tags=["WhatsApp"],
    response_class=PlainTextResponse,
)
def verify_whatsapp_webhook(
    request: Request,
):
    """
    Handle Meta's WhatsApp webhook verification request.

    Configure these values in app/config.py and your environment:
    - whatsapp_verify_token
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    verify_token = getattr(
        settings,
        "whatsapp_verify_token",
        None,
    )

    if (
        mode == "subscribe"
        and verify_token
        and token == verify_token
        and challenge is not None
    ):
        return PlainTextResponse(
            content=challenge,
            status_code=200,
        )

    raise HTTPException(
        status_code=403,
        detail="WhatsApp webhook verification failed.",
    )


# --------------------------------------------------
# 4. WhatsApp Incoming Messages
# --------------------------------------------------

@app.post("/webhook/whatsapp", tags=["WhatsApp"])
async def receive_whatsapp_message(request: Request):
    """
    Placeholder for incoming WhatsApp messages.

    Real message processing is intentionally disabled until
    signature validation, duplicate-message protection,
    and secure message handling are implemented.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "WhatsApp message processing is not implemented yet. "
            "Webhook signature validation and safe message processing "
            "must be configured before enabling this endpoint."
        ),
    )
