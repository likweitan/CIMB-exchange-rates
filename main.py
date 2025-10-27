import os
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from supabase import create_client, Client


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "exchange_rates")

CIMB_URL = "https://www.cimbclicks.com.sg/sgd-to-myr"
WISE_URL = "https://wise.com/gb/currency-converter/sgd-to-myr-rate"


def supabase_configured() -> bool:
    """Check that Supabase credentials look usable."""
    return bool(
        SUPABASE_URL
        and SUPABASE_KEY
        and "YOUR_SUPABASE_URL" not in SUPABASE_URL
        and "YOUR_SUPABASE_KEY" not in SUPABASE_KEY
    )


def insert_into_supabase(rates: List[Dict[str, str]]) -> None:
    """Insert the freshly scraped rates into Supabase."""
    if not rates:
        print("No rates collected; skipping Supabase insert.")
        return

    if not supabase_configured():
        print("Supabase credentials not configured; skipping Supabase insert.")
        return

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        payload = [
            {
                "exchange_rate": rate["exchange_rate"],
                "retrieved_at": rate["timestamp"],
                "platform": rate["platform"],
                "source_url": rate["source_url"],
                "base_currency": "SGD",
                "target_currency": "MYR",
            }
            for rate in rates
        ]
        response = supabase.table(SUPABASE_TABLE).insert(payload).execute()
        print("Inserted into Supabase:", response.data)
    except Exception as exc:
        print(f"Failed to insert into Supabase: {exc}")


def debug_selectors(page, url_label: str, expected_selector: str) -> None:
    """Print helper diagnostics to debug page content and selectors."""
    print(f"\n=== Debugging {url_label} ===")
    content = page.content()
    print("\nPage HTML content preview (first 500 characters):")
    print(content[:500])

    ids = page.eval_on_selector(
        "body",
        """() => {
        const elements = document.querySelectorAll('[id]');
        return Array.from(elements).map(el => el.id);
    }""",
    )
    print("\nAll elements with IDs:")
    print(ids)

    elements = page.query_selector_all(expected_selector)
    print(f"\nNumber of elements matching selector '{expected_selector}': {len(elements)}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debug_page_content_{timestamp}.html"
    with open(filename, "w", encoding="utf-8") as debug_file:
        debug_file.write(content)
    print(f"\nFull page content saved to: {filename}")


def get_exchange_rate() -> None:
    with sync_playwright() as playwright:
        is_ci = (
            os.getenv("CI") == "true"
            or os.getenv("GITHUB_ACTIONS") == "true"
            or not os.getenv("DISPLAY")
        )
        browser = playwright.chromium.launch(
            headless=is_ci,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        )
        rates: List[Dict[str, str]] = []
        timestamp = datetime.utcnow() + timedelta(hours=8)

        try:
            # CIMB rate
            try:
                print("\nAttempting to fetch CIMB rate...")
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    timezone_id="Asia/Singapore",
                    extra_http_headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Cache-Control": "max-age=0",
                    },
                )
                page = context.new_page()
                page.add_init_script(
                    """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {},
                    };
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications'
                        ? Promise.resolve({ state: Notification.permission })
                        : originalQuery(parameters)
                    );
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    delete navigator.__proto__.webdriver;
                """
                )

                page.on(
                    "request", lambda request: print(f"Request: {request.url}")
                )
                page.on(
                    "response",
                    lambda response: print(
                        f"Response: {response.url} - {response.status}"
                    ),
                )

                response = page.goto(CIMB_URL, timeout=60000, wait_until="domcontentloaded")
                print(f"Page response status: {response.status}")

                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(5000)

                # debug_selectors(page, "CIMB", "#rateStr")

                rate_element = page.query_selector("#rateStr")
                if rate_element:
                    text = rate_element.text_content().strip()
                    print(f"Found rate element with text: {text}")
                    match = re.search(r"SGD 1.00 = MYR ([\d\.]+)", text)
                    if match:
                        rates.append(
                            {
                                "exchange_rate": match.group(1),
                                "timestamp": timestamp.isoformat(),
                                "platform": "CIMB",
                                "source_url": CIMB_URL,
                            }
                        )
                        print(f"CIMB Exchange Rate: {match.group(1)}")
                else:
                    print("Rate element not found!")

            except Exception as error:
                print(f"Error fetching CIMB rate: {error}")

            # Wise rate
            try:
                print("\nAttempting to fetch Wise rate...")
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    extra_http_headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                )
                page = context.new_page()
                page.add_init_script(
                    """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {},
                    };
                    delete navigator.__proto__.webdriver;
                """
                )

                response = page.goto(WISE_URL, timeout=60000, wait_until="domcontentloaded")
                print(f"Page response status: {response.status}")

                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(5000)

                # debug_selectors(page, "Wise", "span.text-success")

                selectors = [
                    "span.text-success",
                    "[class*='text-success']",
                    "[data-testid='rate-value']",
                    ".cc__source-to-target__rate",
                    "[class*='rate']",
                ]

                rate_element = None
                for selector in selectors:
                    rate_element = page.query_selector(selector)
                    if rate_element:
                        print(f"Found element with selector: {selector}")
                        break

                if rate_element:
                    wise_rate = rate_element.text_content().strip()
                    print(f"Found rate element with text: {wise_rate}")

                    match = re.search(r"=\s*([\d\.]+)\s*MYR", wise_rate)
                    if match:
                        wise_rate = match.group(1)
                    else:
                        match = re.search(r"(\d+\.\d+)", wise_rate)
                        if match:
                            wise_rate = match.group(1)

                    rates.append(
                        {
                            "exchange_rate": wise_rate,
                            "timestamp": timestamp.isoformat(),
                            "platform": "WISE",
                            "source_url": WISE_URL,
                        }
                    )
                    print(f"WISE Exchange Rate: {wise_rate}")
                else:
                    print("Wise rate element not found!")
                    page.screenshot(
                        path=f"wise_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    )

            except Exception as error:
                print(f"Error fetching Wise rate: {error}")

            if rates:
                existing_data = []
                if os.path.exists("exchange_rates.json"):
                    try:
                        with open("exchange_rates.json", "r", encoding="utf-8") as json_file:
                            content = json_file.read()
                            if content.strip():
                                existing_data = json.loads(content)
                    except json.JSONDecodeError as decode_error:
                        print(f"Warning: Could not parse existing JSON file: {decode_error}")
                        backup_name = f"exchange_rates_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        os.rename("exchange_rates.json", backup_name)
                        existing_data = []

                existing_data.extend(rates)
                with open("exchange_rates.json", "w", encoding="utf-8") as json_file:
                    json.dump(existing_data, json_file, indent=4)
                print("\nExchange rates appended to exchange_rates.json")

                insert_into_supabase(rates)

        finally:
            browser.close()


if __name__ == "__main__":
    get_exchange_rate()
