import requests
from bs4 import BeautifulSoup

# Send a GET request to the CIMB Clicks exchange rate page
url = "https://www.cimbclicks.com.sg/sgd-to-myr"
response = requests.get(url)
print(response)
# Parse the HTML content
soup = BeautifulSoup(response.content, "html.parser")
print(soup)
# Find the element that contains the MYR exchange rate
# This part depends on the structure of the website's HTML
# Replace 'YOUR_SELECTOR_HERE' with the appropriate CSS selector or tag

# Example (assuming the rate is in a span with a specific class):
exchange_rate = soup.select_one("span.class_name_here").text

print("Current SGD to MYR exchange rate:", exchange_rate)