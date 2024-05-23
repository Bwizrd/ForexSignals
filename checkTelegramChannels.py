import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve sensitive information from environment variables
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
channel_ids = os.getenv('CHANNEL_IDS').split(',')  # Assuming CHANNEL_IDS is comma-separated

# Initialize the Telegram client
client = TelegramClient('anon', api_id, api_hash)

async def check_channels():
    await client.start()
    for channel_id in channel_ids:
        try:
            # Attempt to convert to integer if possible, otherwise assume it's a username
            channel_id = int(channel_id) if channel_id.isdigit() else channel_id
            print(f"Checking access to channel: {channel_id}")
            # Fetch only the most recent message to test access
            messages = await client.get_messages(channel_id, limit=1)
            if messages:
                print(f"Access confirmed to channel {channel_id}. Message ID: {messages[0].id}")
            else:
                print(f"No messages received from channel {channel_id}. Check permissions or channel existence.")
        except Exception as e:
            print(f"Failed to access channel {channel_id}: {str(e)}")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_channels())
