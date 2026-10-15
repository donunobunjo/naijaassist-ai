
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row

from app.config import settings
from app.services.db import get_connection


def search_products(
    search: str,
    limit: int = 10,
) -> dict:
    """Search active products and return validated prices."""

    search_term = search.strip()

    if not search_term:
        return {
            "search": search_term,
            "result_count": 0,
            "results": [],
            "data_notice": (
                "Synthetic demonstration data. "
                "Prices and availability are not real retailer offers."
            ),
        }

    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")

    now = datetime.now(timezone.utc)
    price_cutoff = now - timedelta(days=settings.price_freshness_days)

    sql = """
        SELECT
            p.sku, p.brand, p.model, p.category, p.condition,
            p.description, p.ram_gb, p.storage_gb, p.display_inches,
            p.battery_mah, p.camera_mp, p.os, p.connectivity,
            p.warranty_months, pp.price_ngn,
            pp.updated_at AS price_updated_at,
            pp.status AS price_status
        FROM products AS p
        LEFT JOIN product_prices AS pp ON p.sku = pp.sku
        WHERE p.active = TRUE
          AND (
              p.sku ILIKE %s OR p.brand ILIKE %s
              OR p.model ILIKE %s OR p.description ILIKE %s
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
                    (pattern, pattern, pattern, pattern, limit),
                )
                rows = cur.fetchall()
    except psycopg.Error:
        raise

    results = []

    for row in rows:
        updated_at = row["price_updated_at"]
        amount = row["price_ngn"]

        verified = (
            amount is not None
            and row["price_status"] == "approved"
            and updated_at is not None
            and price_cutoff <= updated_at <= now
        )

        results.append({
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
                    if row["display_inches"] is not None else None
                ),
                "battery_mah": row["battery_mah"],
                "camera_mp": (
                    float(row["camera_mp"])
                    if row["camera_mp"] is not None else None
                ),
                "os": row["os"],
                "connectivity": row["connectivity"],
                "warranty_months": row["warranty_months"],
            },
            "price": {
                "amount_ngn": float(Decimal(amount)) if verified else None,
                "currency": "NGN",
                "verified": verified,
                "status": "verified" if verified else "confirmation_required",
                "last_updated": updated_at.isoformat() if updated_at else None,
            },
            "inventory": {
                "available": True,
                "status": "in_stock",
                "note": (
                    "Availability is assumed for demonstration purposes; "
                    "live stock has not been verified."
                ),
            },
        })

    return {
        "search": search_term,
        "result_count": len(results),
        "results": results,
        "data_notice": (
            "Synthetic demonstration data. "
            "Prices and availability are not real retailer offers."
        ),
    }
