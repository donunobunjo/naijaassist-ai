from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal


@dataclass(frozen=True)
class PriceDecision:
    sku: str
    price_ngn: Decimal
    updated_at: datetime
    is_fresh: bool
    message: str


def assess_price(
    sku: str,
    price_ngn: Decimal,
    updated_at: datetime,
    freshness_days: int = 7,
    now: datetime | None = None,
) -> PriceDecision:
    """Assess whether a catalogue price is fresh enough to quote as current.

    A timestamp is necessary but does not itself prove that a price is commercially correct.
    The caller must also ensure the record is approved and came from the trusted database.
    """
    if price_ngn < Decimal("0"):
        raise ValueError("Price cannot be negative")
    if updated_at.tzinfo is None:
        raise ValueError("updated_at must be timezone-aware")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    is_fresh = updated_at >= now - timedelta(days=freshness_days) and updated_at <= now
    if is_fresh:
        message = f"The current recorded price for {sku} is ₦{price_ngn:,.2f}."
    else:
        message = (
            f"The last recorded price for {sku} is ₦{price_ngn:,.2f}, "
            "but it needs confirmation before I can call it current."
        )
    return PriceDecision(sku, price_ngn, updated_at, is_fresh, message)
