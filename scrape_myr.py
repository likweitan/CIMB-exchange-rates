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

        # Go to the CIMB Clicks exchange rate page
        page.goto("https://www.cimbclicks.com.sg/sgd-to-myr")

        # Wait for the page to load the exchange rate (adjust the selector as necessary)
        # Replace 'selector' with the correct CSS selector for the exchange rate
        page.wait_for_selector("#rateStr")

        # Extract the exchange rate using the appropriate selector
        text = page.query_selector("#rateStr").text_content()

        print("CIMB Exchange Rate:", text)

        page = browser.new_page()

        # Navigate to the Revolut currency converter page
        page.goto("https://wise.com/gb/currency-converter/sgd-to-myr-rate")
        
        # Wait for the element to be visible
        page.wait_for_selector("span.text-success:nth-of-type(1)")
        
        # Get the exchange rate element
        exchange_rate_element = page.query_selector("span.text-success:nth-of-type(1)")
        
        # Extract the text content
        wise_rate = exchange_rate_element.text_content()
        
        print(f"WISE Exchange Rate: {wise_rate}")
        # Close the browser
        # browser.close()

        # page = browser.new_page()

        # # Navigate to the Revolut currency converter page
        # page.goto("https://www.pandaremit.com/en/sgp/send-money-to-malaysia")
        
        # # Wait for the element to be visible
        # page.wait_for_selector("p.item-info-amount")
        
        # # Get the exchange rate element
        # # Extract the text content
        # pandaremit_rate = page.eval_on_selector('p.item-info-amount', 'element => element.textContent.trim().split(" ")[0]')
        
        # print(f"pandaremit_rate Exchange Rate: {pandaremit_rate}")
        # Close the browser
        browser.close()

        if text:
            text = text.strip()

                # Extract the exchange rate using regular expression
            match = re.search(r'SGD 1.00 = MYR ([\d\.]+)', text)
            if match:
                rate = match.group(1)  # This will give you '3.2861'

                # Get the current time in UTC and then convert it to UTC+8
                timestamp = datetime.utcnow() + timedelta(hours=8)

                # Prepare the new data record with the UTC+8 timestamp
                new_record = {
                    "exchange_rate": rate,
                    "timestamp": timestamp.isoformat(),
                    "platform": "CIMB"
                }

                # Prepare the new data record with the UTC+8 timestamp
                new_record_wise = {
                    "exchange_rate": wise_rate,
                    "timestamp": timestamp.isoformat(),
                    "platform": "WISE"
                }

                # Check if the JSON file already exists
                if os.path.exists("exchange_rates.json"):
                    # Load the existing data
                    with open("exchange_rates.json", "r") as json_file:
                        data = json.load(json_file)

                # Append the new record to the data list
                data.append(new_record)
                data.append(new_record_wise)
                # data.append(new_record_pandaremit)

                # Save the updated data back to the JSON file
                with open("exchange_rates.json", "w") as json_file:
                    json.dump(data, json_file, indent=4)

                print("Exchange rate appended to exchange_rate.json")
        # if pandaremit_rate:
        #     pandaremit_rate = pandaremit_rate.strip()

        #         # Extract the exchange rate using regular expression
        #     match = re.search(r'(\d+\.\d+)', pandaremit_rate)
        #     if match:
        #         pandaremit_rate = match.group(1)  # This will give you '3.2861'
        #         print(pandaremit_rate)
        #         # Prepare the new data record with the UTC+8 timestamp
        #         new_record_pandaremit = {
        #             "exchange_rate": pandaremit_rate,
        #             "timestamp": timestamp.isoformat(),
        #             "platform": "PANDAREMIT"
        #         }

        #         # Initialize an empty list for records
        #         data = []


                

# To run the function and see the output
# if __name__ == "__main__":
# rate = asyncio.run(get_exchange_rate())
get_exchange_rate()
# print(f"The exchange rate is: {text}")
