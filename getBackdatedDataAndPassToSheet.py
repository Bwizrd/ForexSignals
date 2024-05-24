# import os
# from telethon.sync import TelegramClient
# from telethon.tl.types import MessageMediaPhoto
# import pytz
# from datetime import datetime, timedelta, timezone
# from dotenv import load_dotenv
# import gspread
# from google.oauth2.service_account import Credentials
# import asyncio

# # Load environment variables
# load_dotenv()
# api_id = int(os.getenv('API_ID'))
# api_hash = os.getenv('API_HASH')
# channel_ids = [int(x) for x in os.getenv('CHANNEL_IDS').split(',')]  # Ensure IDs are integers
# sheet_id = os.getenv('SHEET_ID')

# # Setup directories
# base_dir = "MessageData"
# backdated_dir = os.path.join(base_dir, "Backdated_Data")
# os.makedirs(backdated_dir, exist_ok=True)

# # Google Sheets setup
# creds = Credentials.from_service_account_file("credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])
# gspread_client = gspread.authorize(creds)
# workbook = gspread_client.open_by_key(sheet_id)
# sheet = workbook.worksheet("Backdated")

# # Telegram client setup
# client = TelegramClient('session_name', api_id, api_hash)

# async def fetch_messages(client, channel_id, days=7):
#     end_date = datetime.now(timezone.utc)
#     start_date = end_date - timedelta(days=days)
#     all_messages = []

#     # Fetch messages
#     messages = await client.get_messages(channel_id, limit=None, offset_date=end_date)
#     for message in messages:
#         message_date_utc = message.date.astimezone(pytz.utc)
#         if message_date_utc < start_date:
#             break  # Stop fetching older messages
#         all_messages.append(message)
#     return all_messages

# async def log_messages_to_sheet_and_save(messages, directory):
#     for message in messages:
#         date = message.date.astimezone(pytz.timezone('Europe/London'))
#         date_str = date.strftime('%Y-%m-%d %H:%M:%S')
#         text = message.text or ""
#         picture_attached = 'Yes' if isinstance(message.media, MessageMediaPhoto) else 'No'
#         row = [message.id, date_str, text, picture_attached]
#         sheet.append_row(row)  # Appends a row to the Google sheet
        
#         if picture_attached == 'Yes':
#             date_folder = date.strftime('%Y-%m-%d')
#             daily_folder = os.path.join(directory, date_folder)
#             os.makedirs(daily_folder, exist_ok=True)
#             media_path = await message.download_media(file=os.path.join(daily_folder, f"{message.id}.jpg"))
#             print(f"Downloaded media to {media_path}")

# async def main():
#     await client.start()
#     for channel_id in channel_ids:
#         messages = await fetch_messages(client, channel_id)
#         await log_messages_to_sheet_and_save(messages, backdated_dir)
#     await client.disconnect()
#     print("Backdated data has been fetched, logged to the sheet, and saved locally.")

# if __name__ == "__main__":
#     asyncio.run(main())
import asyncio
from telethon import TelegramClient, errors
from dotenv import load_dotenv
import os
import csv
from datetime import datetime, timedelta, timezone
import re

import gspread
from google.oauth2.service_account import Credentials

# Load environment variables from .env file
load_dotenv()

# Retrieve sensitive information from environment variables
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
channel_ids = os.getenv('CHANNEL_IDS').split(',')  # Assuming CHANNEL_IDS is comma-separated
sheet_id = os.getenv('SHEET_ID')
# Initialize the Telegram client
client = TelegramClient('anon', api_id, api_hash)

def setup_google_sheets():
    # Load credentials and authorize with the Google Sheets API
    creds = Credentials.from_service_account_file("credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])
    gspread_client = gspread.authorize(creds)
    return gspread_client

# def create_or_open_sheet(gspread_client, sheet_id, sheet_name):
#     # Open the Google Sheet using the sheet ID
#     try:
#         workbook = gspread_client.open_by_key(sheet_id)
#         sheet = workbook.worksheet(sheet_name)
#     except gspread.exceptions.WorksheetNotFound:
#         # If the worksheet is not found, create a new one
#         sheet = workbook.add_worksheet(title=sheet_name, rows="100", cols="20")
#     return sheet

def create_or_open_sheet(gspread_client, sheet_id, sheet_name):
    # Open the Google Sheet using the sheet ID
    workbook = gspread_client.open_by_key(sheet_id)
    try:
        sheet = workbook.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        # If the worksheet is not found, create a new one
        sheet = workbook.add_worksheet(title=sheet_name, rows="100", cols="20")
        # Define headers for the new sheet
        headers = ["Message ID", "Date", "Source", "Currency Pair", "Entry Price", "Stop Loss", "Take Profits", "Trade Action"]
        sheet.append_row(headers)  # Appends the headers to the new sheet
    else:
        # Check if the existing sheet is empty and add headers if it is
        if sheet.row_count == 1:  # Assumes that if there's only one row, it may need headers
            headers = ["Message ID", "Date", "Source", "Currency Pair", "Entry Price", "Stop Loss", "Take Profits", "Trade Action"]
            sheet.append_row(headers)

    return sheet

def log_signals_to_sheet(sheet, signals):
    # Define headers if the sheet is empty
    if sheet.row_count == 0:
        headers = ["Message ID", "Date", "Source", "Currency Pair", "Entry Price", "Stop Loss", "Take Profits", "Trade Action"]
        sheet.append_row(headers)

    # Log each signal to the Google Sheet
    for signal in signals:
        row = [
            signal["Message ID"],
            signal["Date"],
            signal["source"],
            signal["Currency Pair"],
            signal["Entry Price"],
            signal["Stop Loss"],
            str(signal["Take Profits"]),
            signal["Trade Action"]
        ]
        sheet.append_row(row)
        print(f"Logged data for Message ID {signal['Message ID']}")

def is_trading_signal(text):
    # Exclude messages containing "hit" not followed by "s" or containing "results"
    exclude_pattern = re.compile(
        r"\bhit\b(?!\s*s)|\bresults\b",  # Exclude messages that contain "results"
        re.IGNORECASE
    )

    if exclude_pattern.search(text):
        return False  # If it matches non-instructional patterns, it's not a signal

    # Enhanced regex to broadly capture various formats of trading signals
    signal_pattern = re.compile(
        r"\b(BUY|SELL)\s+.*@\s*\d+(\.\d+)?|"  # Broadly matches "BUY" or "SELL" followed by any characters and a price
        r"\bTP\d?\s*[-:]\s*(open|\d+(\.\d+)?)|"  # Matches "TP" possibly followed by a number or "open"
        r"\bSL\s*[-:]\s*\d+(\.\d+)?"  # Matches "SL" followed by a price
        r"|TP\d+\s+.*\s+SL\s+.*|"  # Matches strings that include "TP" followed by details and "SL"
        r"\bBOS.*-\s*\.\d+,\s*SL\s+\.\d+,\s*TARGET\s+\.\d+"  # Specifically for "BOS - .price, SL .price, TARGET .price"
        r"|\bBOS trade @\s*\.\d+,\s*SL\s+\.\d+,\s*TARGET\s+\.\d+",  # For "BOS trade @ .price, SL .price, TARGET .price"
        re.IGNORECASE
    )
    return bool(signal_pattern.search(text))

async def fetch_and_save_signals():
    await client.start()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)  # Set to 7 days in the past
    for channel_id in channel_ids:
        try:
            channel_id = int(channel_id) if channel_id.isdigit() else channel_id
            channel_entity = await client.get_entity(channel_id)
            channel_name = channel_entity.title.replace('/', '_')  # Sanitize for file naming

            print(f"Fetching trading signals from the past 7 days for channel: {channel_name}")

            # Define file path for CSV using channel name and date
            directory = f"MessageData/Backdated_Data/{channel_name}/{end_date.strftime('%Y-%m-%d')}"
            if not os.path.exists(directory):
                os.makedirs(directory)
            file_path = os.path.join(directory, 'trading_signals.csv')

            # Fetch messages within the date range
            messages = await client.get_messages(channel_id, limit=1000, offset_date=end_date)
            filtered_signals = []
            
            for message in messages:
                if message.date >= start_date:
                    text = message.text.replace('\n', ' ') if message.text else ''
                    if is_trading_signal(text):
                        filtered_signals.append(message)
                    else:
                        print(f"Non-signal message: {text}")  # Print non-signals to console for review

            # Write signals to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['Message ID', 'Date', 'Text'])
                for message in filtered_signals:
                    writer.writerow([message.id, message.date.strftime('%Y-%m-%d %H:%M:%S'), message.text.replace('\n', ' ')])

            print(f"Trading signals saved to {file_path}")

        except errors.ChannelPrivateError:
            print(f"Cannot access private channel: {channel_id}")
        except Exception as e:
            print(f"Failed to fetch messages for channel {channel_id}: {str(e)}")
    await client.disconnect()

def find_latest_folder(base_dir):
    # List all subdirectories in the base directory
    subdirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    # Parse folder names as dates and find the most recent one
    latest_folder = max(subdirs, key=lambda x: datetime.strptime(os.path.basename(x), '%Y-%m-%d'), default=None)
    return latest_folder

def read_signals(csv_file):
    signals = []
    try:
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                signals.append(row)
        print(f"Read {len(signals)} signals from {csv_file}")
    except Exception as e:
        print(f"Failed to read from {csv_file}: {str(e)}")
    return signals

def get_currency_pair(text):
    # List of currency pairs
    currency_pairs = [
        "AUDUSD", "EURCHF", "EURGBP", "EURJPY", "EURUSD",
        "GBPEUR", "GBPUSD", "USDCAD", "USDCHF", "USDJPY", "AUDCAD", "NZDCHF",
        "AUDCNH", "CADCNH", "CNHJPY", "BRLJPY", "GBPINR", "NZDJPY", "AUDNZD",
        "INRJPY", "USDBRL", "USDIDR", "USDINR", "USDKRW", "CHFJPY", "EURNZD",
        "USDPHP", "USDTWD", "EURCNH", "GBPCNH", "NZDCNH", "USDCNH", "XAUUSD"
    ]
    text = text.upper()  # Convert text to upper case to standardize for comparison
    for pair in currency_pairs:
        if pair in text.replace("/", ""):  # Remove slashes for standard format pairs like "EUR/USD" -> "EURUSD"
            return pair
    return None  # Return None if no currency pair is found

def get_trade_action(text, entry, sl):
    # Check if the trade action is explicitly mentioned
    text_upper = text.upper()
    if "BUY" in text_upper:
        return "BUY"
    elif "SELL" in text_upper:
        return "SELL"
    
    # Deduce action based on the numeric values of entry and stop loss
    try:
        entry = float(entry)
        sl = float(sl)
        if sl < entry:
            return "BUY"
        elif sl > entry:
            return "SELL"
    except ValueError:
        # If there's an error in converting strings to floats, we cannot deduce the action
        return None

    return None  # Return None if action cannot be deduced

def get_stop_loss(text):
    # Normalize the text to make regex matching easier
    text = text.replace('SL⛔️', 'SL')  # Replace special SL representations
    text = text.upper()  # Convert text to upper case to handle case insensitivity

    # Regex to find the SL pattern
    # This pattern looks for "SL" followed by optional spaces, possibly a separator like ':', '-', or ' ', and then captures a numeric value
    # The pattern now correctly handles numbers that start with a decimal point
    match = re.search(r"SL\s*[:-]?\s*(-?\d*\.?\d+)", text)
    if match:
        stop_loss_value = match.group(1)
        # Ensure the captured value starts with a '0' if it begins with a decimal point for proper numeric interpretation
        if stop_loss_value.startswith('.'):
            stop_loss_value = '0' + stop_loss_value
        return stop_loss_value

    return None  # Return None if no SL is found

def get_take_profits(text):
    text = text.upper()  # Convert text to upper case for case insensitivity

    # Regex to find TP patterns including "TARGET" as a TP
    tp_patterns = {
        'TP1': r"TP1\s*[:-]?\s*(-?\d*\.?\d+)",
        'TP2': r"TP2\s*[:-]?\s*(-?\d*\.?\d+)",
        'TP3': r"TP3\s*[:-]?\s*(-?\d*\.?\d+)",
        'TP': r"\bTP\b\s*[:-]?\s*(-?\d*\.?\d+)",  # Ensuring it's a standalone TP
        'TARGET': r"TARGET\s*[:-]?\s*(-?\d*\.?\d+)"
    }

    tp_values = {}

    # Search for each TP in the text and add if found
    for tp, pattern in tp_patterns.items():
        match = re.search(pattern, text)
        if match:
            tp_value = match.group(1)
            if tp_value.startswith('.'):  # Handle values that start with a decimal
                tp_value = '0' + tp_value
            tp_values[tp] = tp_value

    # Remove the generic 'TP' if specific TP1, TP2, or TP3 are found
    if any(key in tp_values for key in ['TP1', 'TP2', 'TP3']):
        tp_values.pop('TP', None)  # Remove 'TP' if specific TPs are present

    return tp_values if tp_values else None

def get_entry_price(text):
    matches = re.findall(r'\d*\.\d+|\d+', text)
    if matches:
        entry_price = matches[0]
        # Handle cases where the number starts with a dot (like ".9127")
        if entry_price.startswith('.'):
            entry_price = '0' + entry_price
        return entry_price
    return None


def process_signals(base_dir):
    directories = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    all_signals = []

    for directory in directories:
        short_source = ' '.join(directory.split()[:3])
        full_dir_path = os.path.join(base_dir, directory)
        latest_folder = find_latest_folder(full_dir_path)
        
        if latest_folder:
            csv_file = os.path.join(latest_folder, "trading_signals.csv")
        
            if os.path.exists(csv_file):
                signals = read_signals(csv_file)
                for signal in signals:
                    processed_signal = {
                        "source": short_source,
                        "Message ID": signal["Message ID"],
                        "Date": signal["Date"],
                        "Text": signal["Text"],
                        "Currency Pair": get_currency_pair(signal["Text"]),
                        "Entry Price": get_entry_price(signal["Text"]),
                        "Stop Loss": get_stop_loss(signal["Text"]),
                        "Take Profits": get_take_profits(signal["Text"]),
                        "Trade Action": get_trade_action(signal["Text"], 
                                                         get_entry_price(signal["Text"]), 
                                                         get_stop_loss(signal["Text"]))
                    }
                    all_signals.append(processed_signal)
        else:
            print(f"No latest folder found in: {full_dir_path}")

    return all_signals

def save_signals(signals, save_path):
    keys = signals[0].keys()
    with open(save_path, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(signals)

if __name__ == "__main__":
    # asyncio.run(fetch_and_save_signals()) # Switch off if signals already available
    # base_dir = 'MessageData/Backdated_Data/FOREX SIGNALS GROUP Winning Strategies and Hot Picks!'  # Adjust path as necessary
    # # base_dir = 'MessageData/Backdated_Data/The Charting Society | Free Forex Signal Group'  # Adjust path as necessary
    # # base_dir = 'MessageData/Backdated_Data/Trading Pit Signals ️💎'  # Adjust path as necessary
    # latest_folder = find_latest_folder(base_dir)
    # print("Latest folder:", latest_folder)
    # # Assuming latest_folder is identified
    # csv_file = os.path.join(latest_folder, 'trading_signals.csv')
    # signals = read_signals(csv_file)
    # for signal in signals:
    #     print("Signal", signal)
    #     currency_pair = get_currency_pair(signal["Text"])
    #     print("Currency Pair:", currency_pair)
    #     sl = get_stop_loss(signal["Text"])
    #     print(f"Stop Loss: {sl}")
    #     tps = get_take_profits(signal["Text"])
    #     print(f"Take Profits: {tps}")
    #     entry = get_entry_price(signal["Text"])
    #     print(f"Entry Price: {entry}")
    #     action = get_trade_action(signal["Text"], entry, sl)
    #     print("Trade Action:", action)
    base_dir = 'MessageData/Backdated_Data'
    signals = process_signals(base_dir)
    # print("Signals", signals)
    # Save signals to a CSV file
    today_date_str = datetime.now().strftime('%Y-%m-%d')
    base_save = 'MessageData/ProcessedBackDated'
    save_dir = os.path.join(base_dir, today_date_str)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(base_save, "today's_signals.csv")
    save_signals(signals, save_path)

    print(f"Signals have been saved to {save_path}")
    TODAY_DATE = datetime.now().strftime('%Y-%m-%d')
    SHEET_NAME = f"BackDated_{TODAY_DATE}"  # Dynamic sheet name based on the date
    gspread_client = setup_google_sheets()
    sheet = create_or_open_sheet(gspread_client, sheet_id, SHEET_NAME)
    log_signals_to_sheet(sheet, signals)