import re
import asyncio
import json
import os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# def get_exchange_rate():
#     url = 'https://example.com/exchange-rate'  # Replace with the actual URL

#     browser = await p.chromium.launch()
#     page = await browser.new_page()
#     await page.goto(url)

#         # Wait for the label with id 'rateStr' to be visible
#     await page.wait_for_selector('#rateStr')

#         # Get the text content of the label
#     text = await page.text_content('#rateStr')
#     if text:
#         text = text.strip()

#             # Extract the exchange rate using regular expression
#         match = re.search(r'SGD 1.00 = MYR ([\d\.]+)', text)
#         if match:
#                 rate = match.group(1)  # This will give you '3.2861'
#                 await browser.close()
#                 return rate
#     await browser.close()
#     return None  # Return None if the pattern is not found or the text is None
def debug_selectors(page, url, expected_selector):
    """Helper function to debug page content and selectors"""
    print(f"\n=== Debugging {url} ===")
    
    # Print all HTML content
    content = page.content()
    print("\nPage HTML content preview (first 500 characters):")
    print(content[:500])
    
    # List all elements with ID attributes
    ids = page.eval_on_selector('body', '''() => {
        const elements = document.querySelectorAll('[id]');
        return Array.from(elements).map(el => el.id);
    }''')
    print("\nAll elements with IDs:")
    print(ids)
    
    # Check if our expected selector exists
    elements = page.query_selector_all(expected_selector)
    print(f"\nNumber of elements matching selector '{expected_selector}': {len(elements)}")
    
    # Save full page content to file for further analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debug_page_content_{timestamp}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\nFull page content saved to: {filename}")

def get_exchange_rate():
    with sync_playwright() as p:
        # Detect if running in CI/headless environment
        is_ci = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true' or not os.getenv('DISPLAY')
        
        # Launch browser with stealth settings to avoid bot detection
        browser = p.chromium.launch(
            headless=is_ci,  # Use headless mode in CI, headed mode locally
            args=[
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        )
        rates = []
        timestamp = datetime.utcnow() + timedelta(hours=8)
        
        try:
            # CIMB Rate
            try:
                print("\nAttempting to fetch CIMB rate...")
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    timezone_id='Asia/Singapore',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Cache-Control': 'max-age=0',
                    }
                )
                page = context.new_page()
                
                # Add stealth scripts to hide automation
                page.add_init_script("""
                    // Overwrite the `navigator.webdriver` property to return undefined
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Mock the chrome object
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                    
                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                    );
                    
                    // Overwrite the `plugins` property to use a custom getter.
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Overwrite the `languages` property to use a custom getter.
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Pass the Webdriver Test
                    delete navigator.__proto__.webdriver;
                """)
                
                # Enable request/response logging
                page.on("request", lambda request: print(f"Request: {request.url}"))
                page.on("response", lambda response: print(f"Response: {response.url} - {response.status}"))
                
                response = page.goto("https://www.cimbclicks.com.sg/sgd-to-myr", timeout=60000, wait_until='domcontentloaded')
                print(f"Page response status: {response.status}")
                
                # Wait for network idle and a bit more time for dynamic content
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(5000)  # Wait additional 5 seconds
                
                # Debug page content and selectors
                debug_selectors(page, "CIMB", "#rateStr")
                
                # Try to find the rate element
                rate_element = page.query_selector("#rateStr")
                if rate_element:
                    text = rate_element.text_content().strip()
                    print(f"Found rate element with text: {text}")
                    match = re.search(r'SGD 1.00 = MYR ([\d\.]+)', text)
                    if match:
                        rates.append({
                            "exchange_rate": match.group(1),
                            "timestamp": timestamp.isoformat(),
                            "platform": "CIMB"
                        })
                        print(f"CIMB Exchange Rate: {match.group(1)}")
                else:
                    print("Rate element not found!")

            except Exception as e:
                print(f"Error fetching CIMB rate: {str(e)}")
                import traceback
                print(traceback.format_exc())

            # Wise Rate
            try:
                print("\nAttempting to fetch Wise rate...")
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                    }
                )
                page = context.new_page()
                
                # Add stealth scripts
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                    delete navigator.__proto__.webdriver;
                """)
                
                response = page.goto("https://wise.com/gb/currency-converter/sgd-to-myr-rate", timeout=60000, wait_until='domcontentloaded')
                print(f"Page response status: {response.status}")
                
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(5000)  # Wait additional 5 seconds
                
                # Debug page content and selectors
                debug_selectors(page, "Wise", "span.text-success")
                
                # Try multiple selectors for Wise rate
                rate_element = None
                selectors = [
                    "span.text-success",
                    "[class*='text-success']",
                    "[data-testid='rate-value']",
                    ".cc__source-to-target__rate",
                    "[class*='rate']"
                ]
                
                for selector in selectors:
                    rate_element = page.query_selector(selector)
                    if rate_element:
                        print(f"Found element with selector: {selector}")
                        break
                
                if rate_element:
                    wise_rate = rate_element.text_content().strip()
                    print(f"Found rate element with text: {wise_rate}")
                    
                    # Extract the rate value - looking for pattern like "1 SGD = 3.2527 MYR"
                    match = re.search(r'=\s*([\d\.]+)\s*MYR', wise_rate)
                    if match:
                        wise_rate = match.group(1)
                    else:
                        # Try alternative pattern - just a decimal number
                        match = re.search(r'(\d+\.\d+)', wise_rate)
                        if match:
                            wise_rate = match.group(1)
                    
                    rates.append({
                        "exchange_rate": wise_rate,
                        "timestamp": timestamp.isoformat(),
                        "platform": "WISE"
                    })
                    print(f"WISE Exchange Rate: {wise_rate}")
                else:
                    print("Wise rate element not found!")
                    # Take a screenshot for debugging
                    page.screenshot(path=f"wise_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    
            except Exception as e:
                print(f"Error fetching Wise rate: {str(e)}")
                import traceback
                print(traceback.format_exc())

            # Save results
            if rates:
                data = []
                if os.path.exists("exchange_rates.json"):
                    try:
                        with open("exchange_rates.json", "r") as json_file:
                            content = json_file.read()
                            if content.strip():  # Only parse if file has content
                                data = json.loads(content)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Could not parse existing JSON file: {e}")
                        print("Backing up corrupted file and creating new one...")
                        backup_name = f"exchange_rates_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        os.rename("exchange_rates.json", backup_name)
                        data = []
                
                data.extend(rates)
                
                with open("exchange_rates.json", "w") as json_file:
                    json.dump(data, json_file, indent=4)
                print("\nExchange rates appended to exchange_rates.json")
            
        finally:
            browser.close()

                

# To run the function and see the output
# if __name__ == "__main__":
# rate = asyncio.run(get_exchange_rate())
get_exchange_rate()
# print(f"The exchange rate is: {text}")
