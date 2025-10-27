"""Project-wide configuration values loaded from environment."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE: str = os.getenv("SUPABASE_TABLE", "exchange_rates")

BASE_CURRENCY: str = os.getenv("BASE_CURRENCY", "SGD")
TARGET_CURRENCY: str = os.getenv("TARGET_CURRENCY", "MYR")
