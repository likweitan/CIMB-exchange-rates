import re
import asyncio
import json
import os
from datetime import datetime
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

        # Go to the CIMB Clicks exchange rate page
        page.goto("https://www.cimbclicks.com.sg/sgd-to-myr")

        # Wait for the page to load the exchange rate (adjust the selector as necessary)
        # Replace 'selector' with the correct CSS selector for the exchange rate
        page.wait_for_selector("#rateStr")

        # Extract the exchange rate using the appropriate selector
        text = page.query_selector("#rateStr").text_content()

        print("Current SGD to MYR exchange rate:", text)

        # Close the browser
        browser.close()
        if text:
            text = text.strip()

                # Extract the exchange rate using regular expression
            match = re.search(r'SGD 1.00 = MYR ([\d\.]+)', text)
            if match:
                rate = match.group(1)  # This will give you '3.2861'

                # Prepare the new data record
                new_record = {
                    "exchange_rate": rate,
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Initialize an empty list for records
                data = []

                # Check if the JSON file already exists
                if os.path.exists("exchange_rate.json"):
                    # Load the existing data
                    with open("exchange_rate.json", "r") as json_file:
                        data = json.load(json_file)

                # Append the new record to the data list
                data.append(new_record)

                # Save the updated data back to the JSON file
                with open("exchange_rate.json", "w") as json_file:
                    json.dump(data, json_file, indent=4)

                print("Exchange rate appended to exchange_rate.json")
                return rate

                

# To run the function and see the output
# if __name__ == "__main__":
# rate = asyncio.run(get_exchange_rate())
text = get_exchange_rate()
print(f"The exchange rate is: {text}")
