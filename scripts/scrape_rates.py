"""CLI script to scrape exchange rates and store them locally/Supabase."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.scrapers import collect_rates
from app.services import insert_rates
from app.services.supabase_client import (
    SupabaseConfigurationError,
    supabase_configured,
)

EXCHANGE_RATES_FILE = Path("exchange_rates.json")


def _persist_locally(rates: list[dict[str, str]]) -> None:
    if not rates:
        return

    existing_data: list[dict[str, str]] = []
    if EXCHANGE_RATES_FILE.exists():
        try:
            with EXCHANGE_RATES_FILE.open("r", encoding="utf-8") as json_file:
                content = json_file.read().strip()
                if content:
                    existing_data = json.loads(content)
        except json.JSONDecodeError as decode_error:
            print(f"Warning: Could not parse existing JSON file: {decode_error}")
            backup_name = (
                f"exchange_rates_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            EXCHANGE_RATES_FILE.rename(backup_name)
            existing_data = []

    existing_data.extend(rates)
    with EXCHANGE_RATES_FILE.open("w", encoding="utf-8") as json_file:
        json.dump(existing_data, json_file, indent=4)
    print("\nExchange rates appended to exchange_rates.json")


def main() -> None:
    rates = collect_rates()
    if not rates:
        print("No rates collected; nothing to persist.")
        return

    _persist_locally(rates)

    if not supabase_configured():
        print("Supabase credentials not configured; skipping Supabase insert.")
        return

    try:
        response = insert_rates(rates)
        print("Inserted into Supabase:", response)
    except SupabaseConfigurationError as exc:
        print(f"Supabase configuration error: {exc}")
    except Exception as exc:  # pragma: no cover - defensive logging path
        print(f"Failed to insert into Supabase: {exc}")


if __name__ == "__main__":
    main()
