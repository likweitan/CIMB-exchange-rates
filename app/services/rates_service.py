"""Business logic for working with exchange rates."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from config import BASE_CURRENCY, TARGET_CURRENCY
from . import supabase_client


def insert_rates(rates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Insert rates after enriching with base/target currencies."""
    if not rates:
        return []

    enriched = [
        {
            **rate,
            "base_currency": rate.get("base_currency", BASE_CURRENCY),
            "target_currency": rate.get("target_currency", TARGET_CURRENCY),
        }
        for rate in rates
    ]
    return supabase_client.insert_rows(enriched)


def get_rates(limit: int | None = None) -> list[dict[str, Any]]:
    """Return exchange rates ordered newest first."""
    return supabase_client.fetch_rows(limit=limit)


def get_latest_rates() -> list[dict[str, Any]]:
    """Return the most recent rate per platform."""
    latest: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    for row in get_rates():
        platform = row.get("platform")
        if platform not in latest:
            latest[platform] = row
    return list(latest.values())
