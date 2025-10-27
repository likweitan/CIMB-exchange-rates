"""Supabase client helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable, Sequence

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_TABLE, SUPABASE_URL


class SupabaseConfigurationError(RuntimeError):
    """Raised when Supabase credentials are missing or invalid."""


def supabase_configured() -> bool:
    """Return True when Supabase credentials appear usable."""
    return bool(
        SUPABASE_URL
        and SUPABASE_KEY
        and "YOUR_SUPABASE_URL" not in SUPABASE_URL
        and "YOUR_SUPABASE_KEY" not in SUPABASE_KEY
    )


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Return a cached Supabase client instance."""
    if not supabase_configured():
        raise SupabaseConfigurationError(
            "Supabase credentials are not configured. Check your environment variables."
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def insert_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Insert rows into the exchange rates table."""
    if not rows:
        return []
    response = get_client().table(SUPABASE_TABLE).insert(rows).execute()
    return response.data or []


def fetch_rows(limit: int | None = None) -> list[dict[str, Any]]:
    """Fetch rows ordered by most recent first."""
    query = (
        get_client()
        .table(SUPABASE_TABLE)
        .select("*")
        .order("retrieved_at", desc=True)
    )
    if limit:
        query = query.limit(limit)
    response = query.execute()
    return response.data or []
