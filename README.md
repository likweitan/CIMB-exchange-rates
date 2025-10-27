# SGD-MYR Exchange Rates Scraper

Python Playwright scraper with Supabase integration that tracks SGD to MYR exchange rates from CIMB Clicks and Wise, persists snapshots locally, and ships fresh readings to Supabase.

## What It Does

- Launches Chromium via Playwright with light anti-bot hardening.
- Scrapes CIMB Clicks (`sgd-to-myr`) and Wise (`currency-converter/sgd-to-myr-rate`) for the current rate.
- Saves a running history to `exchange_rates.json` and inserts each run into a Supabase table (defaults to `exchange_rates`).
- Provides optional debug artifacts (HTML dumps / screenshots) when selectors fail so you can diagnose page changes quickly.

## Requirements

- Python 3.10+
- pip (bundled with Python)
- Playwright browser binaries (`playwright install`)
- Supabase project (optional but recommended for persistence)

## Setup

1. Clone the repository and move into the project folder.
2. (Optional) Create a virtual environment: `python -m venv venv && source venv/bin/activate` on macOS/Linux or `venv\\Scripts\\activate` on Windows.
3. Install dependencies: `python -m pip install -r requirements.txt`.
4. Install browser drivers: `playwright install`.
5. Copy `.env.example` to `.env` (or create `.env`) and supply your Supabase credentials:
   ```ini
   SUPABASE_URL=https://YOUR-PROJECT.supabase.co
   SUPABASE_KEY=YOUR_SERVICE_ROLE_OR_ANON_KEY
   SUPABASE_TABLE=exchange_rates  # optional override
   ```
   Without credentials the scraper still writes to `exchange_rates.json` but skips Supabase inserts.

## Running the Scraper

- Manual run: `python main.py`
- The script prints the collected rates, updates `exchange_rates.json`, and posts new records to Supabase if credentials exist.
- Inspect newly created `debug_page_content_*.html` files or screenshots when a selector cannot be found.

## Automation

- `.github/workflows/update_exchange_rates.yml` schedules the scraper to run in GitHub Actions. Ensure repository secrets `SUPABASE_URL` and `SUPABASE_KEY` are configured before enabling the workflow.

## Troubleshooting

- **Selectors failing:** open the latest `debug_page_content_*.html` to update CSS selectors in `main.py`.
- **Supabase insert skipped:** confirm `.env` is loaded (the script now runs `load_dotenv()`), and verify credentials are correct and have insert permissions.
- **Playwright issues:** rerun `playwright install` after dependency upgrades, and ensure headless mode is allowed in your environment (CI uses headless automatically).

## License

MIT. See `LICENSE` if provided, otherwise assume standard MIT usage rights.
