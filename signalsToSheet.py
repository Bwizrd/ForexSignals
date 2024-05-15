import csv
import os
from collections import defaultdict
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Initialize and load environment variables
load_dotenv()

# Google Sheets setup
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)
workbook = client.open_by_key(os.getenv('SHEET_ID'))  # Ensure SHEET_ID is correctly set in your .env file

# Function to categorize messages
def categorize_message(text):
    idea_keywords = ['potential', 'trading idea']
    if any(keyword in text.lower() for keyword in idea_keywords):
        return 'ideas'
    elif is_trading_signal(text):
        return 'signals'
    else:
        return 'other'

# Function to check if a message is a trading signal
def is_trading_signal(text):
    # Extend action keywords to include simpler direct commands and encouraging phrases
    action_keywords = ['buy now', 'sell now', 'place buy order', 'place sell order', 'buy', 'sell', "let's go", "go for"]
    exclusion_phrases = [
        'hits target', 'did you get in', 'continues into profit', 'moving stop to',
        'where we are likely to see', 'to lock in profits', 'potential buying opportunity'  # Exclude speculative language
    ]
    # Convert text to lowercase for case insensitive matching
    text_lower = text.lower()
    # Check if any exclusion phrases are present
    if any(phrase in text_lower for phrase in exclusion_phrases):
        return False  # Exclude texts that contain these phrases
    # Check for presence of action keywords directly
    if any(keyword in text_lower for keyword in action_keywords):
        return True
    # Additional check for context keywords only if followed by specifics like prices or conditions
    context_keywords = ['target', 'SL']  # Used in conjunction with action keywords
    if any(keyword in text_lower for keyword in context_keywords):
        if any(char.isdigit() for char in text_lower):  # Ensure there are numbers following the context keyword
            return True
    return False

# Read CSV data
data_file = 'messages_data.csv'
data_by_date = defaultdict(lambda: {'signals': [], 'other': [], 'ideas': []})

# Parse CSV and categorize messages
with open(data_file, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        category = categorize_message(row['text'])
        data_by_date[row['date']][category].append(row)

# Base directory for message data
base_dir = 'messageData'

# Create directories and save data, also update Google Sheets
for date, categories in data_by_date.items():
    date_dir = os.path.join(base_dir, date.replace('-', ''))
    os.makedirs(date_dir, exist_ok=True)
    # Handle directories and Google Sheets for each category
    for category in ['signals', 'other', 'ideas']:
        category_dir = os.path.join(date_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        # CSV file path
        csv_file_path = os.path.join(category_dir, f"{category}.csv")
        # Save to CSV
        if categories[category]:
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(categories[category])
            print(f"Data for {date} in category '{category}' written to {csv_file_path}.")
        # Create or clear Google Sheets worksheet
        worksheet_name = f"{date.replace('-', '')}_{category}"
        try:
            sheet = workbook.worksheet(worksheet_name)
            sheet.clear()  # Clear if exists
        except gspread.WorksheetNotFound:
            sheet = workbook.add_worksheet(title=worksheet_name, rows="100", cols="10")
        # Populate Google Sheets
        field_names = reader.fieldnames
        sheet.append_row(field_names)  # Append header
        for signal in categories[category]:
            row = [signal[field] for field in field_names]
            sheet.append_row(row)
        print(f"Google Sheet for {date} in category '{category}' updated with data.")
