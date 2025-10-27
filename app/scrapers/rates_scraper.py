"""Playwright-powered scrapers for collecting exchange rates."""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

CIMB_URL = "https://www.cimbclicks.com.sg/sgd-to-myr"
WISE_URL = "https://wise.com/gb/currency-converter/sgd-to-myr-rate"
WESTERNUNION_URL = (
    "https://www.westernunion.com/sg/en/currency-converter/sgd-to-myr-rate.html"
)


def debug_selectors(page: Page, url_label: str, expected_selector: str) -> None:
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


def _new_context(browser: Browser) -> BrowserContext:
    return browser.new_context(
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
        },
    )


def _launch_browser():
    playwright = sync_playwright().start()
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
    return playwright, browser


def _extract_rate_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = re.search(r"([\d]+(?:[.,]\d+)?)", text)
    if match:
        return match.group(1).replace(",", "")
    return None


def _scrape_cimb(browser: Browser, timestamp: datetime, rates: List[Dict[str, str]]) -> None:
    print("\nAttempting to fetch CIMB rate...")
    context: Optional[BrowserContext] = None
    try:
        context = _new_context(browser)
        page = context.new_page()

        def log_response(response):
            if "cimbrate" in response.url.lower():
                print(f"[CIMB][response] {response.status} {response.url}")

        page.on("response", log_response)

        print("Navigating to CIMB URL...")
        page.goto(CIMB_URL, wait_until="networkidle", timeout=60000)

        rate_elements = page.query_selector_all("span.exchAnimate")
        parsed_rate = None
        for element in rate_elements:
            text = element.text_content().strip()
            parsed_rate = _extract_rate_text(text)
            if parsed_rate:
                break

        if parsed_rate:
            print(f"CIMB Exchange Rate: {parsed_rate}")
            rates.append(
                {
                    "exchange_rate": parsed_rate,
                    "timestamp": timestamp.isoformat(),
                    "platform": "CIMB",
                }
            )
        else:
            print("CIMB rate element not found or unparsable!")
            debug_selectors(page, "CIMB", "span.exchAnimate")
    except PlaywrightTimeoutError as error:
        print(f"CIMB scraping timed out: {error}")
    except Exception as error:
        print(f"Error fetching CIMB rate: {error}")
    finally:
        if context:
            context.close()


def _scrape_wise(browser: Browser, timestamp: datetime, rates: List[Dict[str, str]]) -> None:
    print("\nAttempting to fetch Wise rate...")
    context: Optional[BrowserContext] = None
    try:
        context = _new_context(browser)
        page = context.new_page()

        def log_console_message(msg):
            if msg.type == "error":
                print(f"[Wise console:{msg.type}] {msg.text}")

        page.on("console", log_console_message)

        print("Navigating to Wise URL...")
        page.goto(WISE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=30000)

        selectors = [
            "[data-testid='cc__converter']//div[contains(@class,'text-success')]",
            "span[data-testid='cc__rate_string']",
            "span.cc__RateString-sc",
        ]

        parsed_rate = None
        for selector in selectors:
            element = page.query_selector(selector)
            if element:
                text = element.text_content().strip()
                parsed_rate = _extract_rate_text(text)
                if parsed_rate:
                    print(f"Found rate element on Wise with selector {selector}: {text}")
                    break

        if parsed_rate:
            print(f"Wise Exchange Rate: {parsed_rate}")
            rates.append(
                {
                    "exchange_rate": parsed_rate,
                    "timestamp": timestamp.isoformat(),
                    "platform": "WISE",
                }
            )
        else:
            print("Wise rate element not found or unparsable!")
            debug_selectors(page, "Wise", "[data-testid='cc__rate_string']")
    except PlaywrightTimeoutError as error:
        print(f"Wise scraping timed out: {error}")
    except Exception as error:
        print(f"Error fetching Wise rate: {error}")
    finally:
        if context:
            context.close()


def _scrape_western_union(
    browser: Browser, timestamp: datetime, rates: List[Dict[str, str]]
) -> None:
    print("\nAttempting to fetch Western Union rate...")
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    try:
        context = _new_context(browser)
        context.add_cookies(
            [
                {
                    "name": "policy",
                    "value": "true",
                    "domain": ".westernunion.com",
                    "path": "/",
                }
            ]
        )
        page = context.new_page()

        def log_console_message(msg):
            if msg.type == "error":
                print(f"[WesternUnion console:{msg.type}] {msg.text}")

        def log_response(response):
            if "currency" in response.url.lower():
                print(f"[WesternUnion response] {response.status} {response.url}")

        def log_failed_request(request):
            print(
                f"[WesternUnion request failed] {request.method} {request.url} - {request.failure}"
            )

        def capture_debug(label: str) -> None:
            if not page:
                return
            try:
                debug_selectors(page, f"Western Union {label}", "span.fx-to")
            except Exception as debug_error:
                print(f"[WesternUnion debug capture error] {debug_error}")

        page.on("console", log_console_message)
        page.on("response", log_response)
        page.on("request_failed", log_failed_request)

        print("Navigating to Western Union URL...")
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

        try:
            response = page.goto(
                WESTERNUNION_URL, timeout=60000, wait_until="domcontentloaded"
            )
        except PlaywrightTimeoutError as navigation_error:
            print(
                "Western Union navigation timed out while waiting for domcontentloaded; capturing diagnostics and continuing."
            )
            capture_debug("(navigation timeout)")
            response = None

        if response:
            print(f"Page response status: {response.status}")
        else:
            print("Page response status: No response object returned by Playwright.")

        try:
            page.wait_for_load_state("networkidle", timeout=30000)
            print("Western Union page reached 'networkidle' state.")
        except PlaywrightTimeoutError as timeout_error:
            print(
                "Western Union page did not reach 'networkidle' within 30s; capturing diagnostics and continuing."
            )
            capture_debug("(networkidle timeout)")

        page.wait_for_timeout(5000)

        selectors = [
            "span.fx-to",
            "[class*='fx-to']",
            "[data-testid*='fx-to']",
            "[class*='currency'] span",
        ]

        parsed_rate = None
        for selector in selectors:
            rate_element = page.query_selector(selector)
            if rate_element:
                text = rate_element.text_content().strip()
                parsed_rate = _extract_rate_text(text)
                if parsed_rate:
                    print(f"Found rate element with selector: {selector}")
                    break

        if parsed_rate:
            print(f"Western Union Exchange Rate: {parsed_rate}")
            rates.append(
                {
                    "exchange_rate": parsed_rate,
                    "timestamp": timestamp.isoformat(),
                    "platform": "WESTERNUNION",
                }
            )
        else:
            print("Western Union rate element not found or unparsable!")
            capture_debug("(unparsed rate)")

    except PlaywrightTimeoutError as error:
        print(f"Western Union scraping timed out: {error}")
    except Exception as error:
        print(f"Error fetching Western Union rate: {error}")
    finally:
        if page:
            page.close()
        if context:
            context.close()


def collect_rates() -> List[Dict[str, str]]:
    """Collect exchange rates from the supported providers."""
    playwright = None
    browser = None
    try:
        playwright, browser = _launch_browser()
        rates: List[Dict[str, str]] = []
        timestamp = datetime.utcnow() + timedelta(hours=8)

        _scrape_cimb(browser, timestamp, rates)
        _scrape_wise(browser, timestamp, rates)
        _scrape_western_union(browser, timestamp, rates)

        return rates
    finally:
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
