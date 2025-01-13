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
def get_exchange_rate():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Go to the CIMB Clicks exchange rate page
            page.goto("https://www.cimbclicks.com.sg/sgd-to-myr")

            # Wait for the exchange rate to appear (updating selector and adding longer timeout)
            page.wait_for_selector(".exchange-rate-value", timeout=60000)
            
            # Extract the exchange rate using the updated selector
            text = page.query_selector(".exchange-rate-value").text_content()
            
            print("CIMB Exchange Rate:", text)

            # Open new page for Wise
            page = browser.new_page()
            page.goto("https://wise.com/gb/currency-converter/sgd-to-myr-rate")
            
            # Wait for the Wise rate with longer timeout
            page.wait_for_selector("span.text-success:nth-of-type(1)", timeout=60000)
            wise_rate = page.query_selector("span.text-success:nth-of-type(1)").text_content()
            
            print(f"WISE Exchange Rate: {wise_rate}")

            if text:
                text = text.strip()
                # Extract the exchange rate using regular expression
                match = re.search(r'(\d+\.\d+)', text)
                if match:
                    rate = match.group(1)

                    # Get the current time in UTC+8
                    timestamp = datetime.utcnow() + timedelta(hours=8)

                    # Prepare the records
                    new_record = {
                        "exchange_rate": rate,
                        "timestamp": timestamp.isoformat(),
                        "platform": "CIMB"
                    }

                    new_record_wise = {
                        "exchange_rate": wise_rate,
                        "timestamp": timestamp.isoformat(),
                        "platform": "WISE"
                    }

                    # Initialize data list
                    data = []
                    
                    # Load existing data if file exists
                    if os.path.exists("exchange_rates.json"):
                        with open("exchange_rates.json", "r") as json_file:
                            data = json.load(json_file)

                    # Append new records
                    data.append(new_record)
                    data.append(new_record_wise)

                    # Save to file
                    with open("exchange_rates.json", "w") as json_file:
                        json.dump(data, json_file, indent=4)

                    print("Exchange rates appended to exchange_rates.json")

        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            browser.close()

# To run the function and see the output
# if __name__ == "__main__":
# rate = asyncio.run(get_exchange_rate())
get_exchange_rate()
# print(f"The exchange rate is: {text}")
