from datetime import datetime, timedelta, timezone
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.services.db import get_connection


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description=(
        "API for the fictional NaijaMobile Hub customer-service assistant. "
        "All catalogue data is synthetic demonstration data."
    ),
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/products")
def search_products(
    search: str = Query(
        min_length=1,
        max_length=100,
        description="Search by product name, brand, SKU, or description.",
    ),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Search the catalogue and return product details, prices, and demo availability."""

    search_term = search.strip()

    if not search_term:
        raise HTTPException(
            status_code=422,
            detail="Search term cannot be empty.",
        )

    now = datetime.now(timezone.utc)
    price_cutoff = now - timedelta(
        days=settings.price_freshness_days
    )

    sql = """
        SELECT
            p.sku,
            p.brand,
            p.model,
            p.category,
            p.condition,
            p.description,
            p.ram_gb,
            p.storage_gb,
            p.display_inches,
            p.battery_mah,
            p.camera_mp,
            p.os,
            p.connectivity,
            p.warranty_months,
            pp.price_ngn,
            pp.updated_at AS price_updated_at,
            pp.status AS price_status
        FROM products AS p
        LEFT JOIN product_prices AS pp
            ON p.sku = pp.sku
        WHERE p.active = TRUE
          AND (
              p.sku ILIKE %s
              OR p.brand ILIKE %s
              OR p.model ILIKE %s
              OR p.description ILIKE %s
          )
        ORDER BY p.brand, p.model
        LIMIT %s
    """

    pattern = f"%{search_term}%"

    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    sql,
                    (
                        pattern,
                        pattern,
                        pattern,
                        pattern,
                        limit,
                    ),
                )
                rows = cur.fetchall()

    except psycopg.Error:
        # Do not expose database credentials or connection details to clients.
        raise HTTPException(
            status_code=503,
            detail="The product catalogue is temporarily unavailable.",
        ) from None

    results = []

    for row in rows:
        price_updated_at = row["price_updated_at"]
        price = row["price_ngn"]

        price_verified = (
            price is not None
            and row["price_status"] == "approved"
            and price_updated_at is not None
            and price_cutoff <= price_updated_at <= now
        )

        results.append(
            {
                "sku": row["sku"],
                "brand": row["brand"],
                "model": row["model"],
                "category": row["category"],
                "condition": row["condition"],
                "description": row["description"],
                "specifications": {
                    "ram_gb": row["ram_gb"],
                    "storage_gb": row["storage_gb"],
                    "display_inches": (
                        float(row["display_inches"])
                        if row["display_inches"] is not None
                        else None
                    ),
                    "battery_mah": row["battery_mah"],
                    "camera_mp": (
                        float(row["camera_mp"])
                        if row["camera_mp"] is not None
                        else None
                    ),
                    "os": row["os"],
                    "connectivity": row["connectivity"],
                    "warranty_months": row["warranty_months"],
                },
                "price": {
                    "amount_ngn": (
                        float(Decimal(price))
                        if price_verified
                        else None
                    ),
                    "currency": "NGN",
                    "verified": price_verified,
                    "status": (
                        "verified"
                        if price_verified
                        else "confirmation_required"
                    ),
                    "last_updated": (
                        price_updated_at.isoformat()
                        if price_updated_at is not None
                        else None
                    ),
                },
                "inventory": {
                    "available": True,
                    "status": "in_stock",
                    "note": (
                        "Availability is assumed for demonstration purposes; "
                        "live stock has not been verified."
                    ),
                },
            }
        )

    return {
        "search": search_term,
        "result_count": len(results),
        "results": results,
        "data_notice": (
            "Synthetic demonstration data. "
            "Prices and availability are not real retailer offers."
        ),
    }


@app.get("/webhooks/whatsapp", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(
        default=None,
        alias="hub.verify_token",
    ),
    hub_challenge: str | None = Query(
        default=None,
        alias="hub.challenge",
    ),
):
    """Verify the Meta webhook challenge."""

    if (
        hub_mode == "subscribe"
        and settings.whatsapp_verify_token
        and hub_verify_token == settings.whatsapp_verify_token
        and hub_challenge is not None
    ):
        return hub_challenge

    raise HTTPException(
        status_code=403,
        detail="Webhook verification failed",
    )


@app.post("/webhooks/whatsapp")
async def receive_whatsapp_webhook(request: Request):
    """
    Placeholder only.

    Inbound message processing remains disabled until signature verification,
    event deduplication, and safe message processing are implemented.
    """

    await request.body()

    raise HTTPException(
        status_code=501,
        detail="Inbound WhatsApp message processing is not implemented yet.",
    )