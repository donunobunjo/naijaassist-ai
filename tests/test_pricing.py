from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest
from app.services.pricing import assess_price


def test_fresh_price_is_fresh():
    now = datetime(2026, 10, 14, tzinfo=timezone.utc)
    result = assess_price("NMH-PHN-0001", Decimal("250000"), now, now=now)
    assert result.is_fresh is True
    assert "₦250,000.00" in result.message


def test_old_price_is_stale():
    now = datetime(2026, 10, 14, tzinfo=timezone.utc)
    old = now - timedelta(days=8)
    result = assess_price("NMH-PHN-0001", Decimal("250000"), old, now=now)
    assert result.is_fresh is False
    assert "needs confirmation" in result.message


def test_negative_price_rejected():
    with pytest.raises(ValueError):
        assess_price("NMH-PHN-0001", Decimal("-1"), datetime.now(timezone.utc))


def test_naive_timestamp_rejected():
    with pytest.raises(ValueError):
        assess_price("NMH-PHN-0001", Decimal("100"), datetime(2026, 10, 14))
