
from datetime import datetime
from decimal import Decimal

from app.services.products import search_products
from app.services.pricing import assess_price


def format_naira(amount: int | float) -> str:
    """Format a numeric price in Nigerian naira."""
    return f"₦{amount:,.2f}" if amount % 1 else f"₦{amount:,.0f}"


def answer_price_question(product_query: str) -> str:
    """Answer a product-price question using catalogue results."""

    if not product_query or not product_query.strip():
        return (
            "Please provide the phone model or product SKU "
            "so I can check its price."
        )

    response = search_products(
        search=product_query.strip(),
        limit=10,
    )
    products = response.get("results", [])

    if not products:
        return (
            "I couldn't find that product in our catalogue. "
            "Please check the model name or SKU."
        )

    # Ask the customer to clarify ambiguous searches.
    if len(products) > 1:
        matches = [
            f"- {p['brand']} {p['model']} (SKU: {p['sku']})"
            for p in products[:5]
        ]

        return (
            "I found several matching products. Which one do you mean?\n"
            + "\n".join(matches)
        )

    product = products[0]
    price = product.get("price") or {}

    # Never quote an unapproved, missing, or unverified price.
    if (
        price.get("verified") is not True
        or price.get("status") not in {"verified", "approved"}
        or price.get("amount_ngn") is None
        or not price.get("last_updated")
    ):
        return (
            f"I couldn't verify a current price for "
            f"{product['brand']} {product['model']}. "
            "Please let our support team confirm it."
        )

    try:
        updated_at = datetime.fromisoformat(
            price["last_updated"].replace("Z", "+00:00")
        )

        decision = assess_price(
            sku=product["sku"],
            price_ngn=Decimal(str(price["amount_ngn"])),
            updated_at=updated_at,
        )

    except (ValueError, TypeError):
        return (
            f"I couldn't verify a current price for "
            f"{product['brand']} {product['model']}. "
            "Please let our support team confirm it."
        )

    if not decision.is_fresh:
        return (
            f"I couldn't confirm that the recorded price for "
            f"{product['brand']} {product['model']} "
            "is current. Please let our support team confirm it."
        )

    return (
        f"The listed price for {product['brand']} {product['model']} "
        f"(SKU: {product['sku']}) is "
        f"{format_naira(price['amount_ngn'])}. "
        f"Last updated: {price['last_updated']}. "
        "Please note that this is synthetic demonstration data, "
        "not a real retailer offer."
    )
