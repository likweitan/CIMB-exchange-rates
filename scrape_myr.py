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
        browser = p.chromium.launch(headless=False)  # Set to False to see the browser
        rates = []
        timestamp = datetime.utcnow() + timedelta(hours=8)
        
        try:
            # CIMB Rate
            try:
                print("\nAttempting to fetch CIMB rate...")
                page = browser.new_page()
                
                # Enable request/response logging
                page.on("request", lambda request: print(f"Request: {request.url}"))
                page.on("response", lambda response: print(f"Response: {response.url} - {response.status}"))
                
                response = page.goto("https://www.cimbclicks.com.sg/sgd-to-myr", timeout=60000)
                print(f"Page response status: {response.status}")
                
                # Wait for network idle and a bit more time for dynamic content
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(5000)  # Wait additional 5 seconds
                
                # Debug page content and selectors
                #debug_selectors(page, "CIMB", "#rateStr")
                
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
                page = browser.new_page()
                response = page.goto("https://wise.com/gb/currency-converter/sgd-to-myr-rate", timeout=60000)
                print(f"Page response status: {response.status}")
                
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(5000)  # Wait additional 5 seconds
                
                # Debug page content and selectors
                debug_selectors(page, "Wise", "span.text-success:nth-of-type(1)")
                
                rate_element = page.query_selector("span.text-success:nth-of-type(1)")
                if rate_element:
                    wise_rate = rate_element.text_content().strip()
                    print(f"Found rate element with text: {wise_rate}")
                    rates.append({
                        "exchange_rate": wise_rate,
                        "timestamp": timestamp.isoformat(),
                        "platform": "WISE"
                    })
                    print(f"WISE Exchange Rate: {wise_rate}")
                else:
                    print("Wise rate element not found!")
                    
            except Exception as e:
                print(f"Error fetching Wise rate: {str(e)}")
                import traceback
                print(traceback.format_exc())

            # Save results
            if rates:
                data = []
                if os.path.exists("exchange_rates.json"):
                    with open("exchange_rates.json", "r") as json_file:
                        data = json.load(json_file)
                
                data.extend(rates)
                
                with open("exchange_rates.json", "w") as json_file:
                    json.dump(data, json_file, indent=4)
                print("\nExchange rates appended to exchange_rates.json")
            
        finally:
            # Give time to see the pages if needed
            print("\nWaiting 10 seconds before closing browser...")
            page.wait_for_timeout(10000)
            browser.close()

                

# To run the function and see the output
# if __name__ == "__main__":
# rate = asyncio.run(get_exchange_rate())
get_exchange_rate()
# print(f"The exchange rate is: {text}")
