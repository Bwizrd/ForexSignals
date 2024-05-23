from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto
import csv
import os
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve sensitive information from environment variables
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
channel_ids = [int(id) for id in os.getenv('CHANNEL_IDS').split(',')]  # Handling multiple channels

download_directory = 'downloaded_images/'

# Ensure the download directory exists
if not os.path.exists(download_directory):
    os.makedirs(download_directory)

local_timezone = pytz.timezone('Europe/London')

# Initialize the Telegram client
client = TelegramClient('anon', api_id, api_hash)

client.start()

messages_data = []  # List to hold message data dictionaries

for channel_id in channel_ids:
    print(f"Fetching messages from channel {channel_id}")
    with client:
        for message in client.iter_messages(channel_id, limit=5):  # Adjust limit as needed
            local_date = message.date.astimezone(local_timezone)
            timestamp = local_date.strftime('%Y%m%d_%H%M%S')
            message_data = {
                'channel_id': channel_id,
                'date': local_date.strftime('%Y-%m-%d'),
                'time': local_date.strftime('%H:%M:%S'),
                'picture_attached': isinstance(message.media, MessageMediaPhoto),
                'file_path': '',
                'text': message.text or ''
            }

            if message_data['picture_attached']:
                file_name = f"{timestamp}.jpg"
                save_path = os.path.join(download_directory, file_name)
                client.download_media(message.media, file=save_path)
                message_data['file_path'] = save_path

            messages_data.append(message_data)
            print(f"Message collected: {message_data}")

# Define the CSV file name
csv_file_name = 'messages_data3.csv'

# Field names in the CSV file
field_names = ['channel_id', 'date', 'time', 'picture_attached', 'file_path', 'text']

# Writing to a CSV file
with open(csv_file_name, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=field_names)
    writer.writeheader()
    for message_data in messages_data:
        writer.writerow({
            'channel_id': message_data['channel_id'],
            'date': message_data['date'],
            'time': message_data['time'],
            'picture_attached': message_data['picture_attached'],
            'file_path': message_data['file_path'],
            'text': message_data['text'].replace('\n', ' ')  # Optionally replace newlines with spaces
        })

print(f"Data written to {csv_file_name}")
