import discord
import requests
from bs4 import BeautifulSoup
import re
import schedule
import time
import asyncio

intents = discord.Intents.default()
client = discord.Client(intents=intents)

TOKEN = 'your_discord_bot_token'  # Replace with your bot's token
CHANNEL_ID = your_channel_id  # Replace with the channel ID where you want to send the message

def get_exchange_rate():
    url = 'https://www.cimbclicks.com.sg/sgd-to-myr-business'  # Replace with the actual URL
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Modify this part based on the actual HTML structure of the page
    text = soup.find('div', class_='exchange-rate').text.strip()

    # Extract the exchange rate using regular expression
    match = re.search(r'SGD 1.00 = MYR ([\d\.]+)', text)
    if match:
        rate = match.group(1)  # This will give you '3.2861'
        return rate
    else:
        return None

async def send_exchange_rate():
    channel = client.get_channel(CHANNEL_ID)
    rate = get_exchange_rate()
    if rate:
        await channel.send(f"The current exchange rate is {rate}")
    else:
        await channel.send("Failed to retrieve the exchange rate.")

def schedule_jobs():
    schedule.every().hour.do(lambda: asyncio.run_coroutine_threadsafe(send_exchange_rate(), client.loop))

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    schedule_jobs()

    # Start the scheduler in a separate thread so it doesn't block the bot
    while True:
        schedule.run_pending()
        time.sleep(1)

client.run(TOKEN)