import gspread
from google.oauth2.service_account import Credentials
import csv
import time
import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)

sheet_id = int(os.getenv('SHEET_ID'))
workbook = client.open_by_key(sheet_id)

values_list = workbook.sheet1.row_values(1)
# print(values_list)

csv_file_path = 'messages_data.csv'

worksheet_list = map(lambda x: x.title, workbook.worksheets())
print(list(worksheet_list))

sheet = workbook.worksheet("TestSheet")

with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file)
    data = list(csv_reader)  # Convert CSV rows to a list

# Clear existing content in the sheet (optional)
sheet.clear()

sheet.update('A1', data)
# Upload CSV data to Google Sheet
# for row_index, row in enumerate(rows, start=1):
#     time.sleep(1)
#     sheet.insert_row(row, row_index)

print("CSV data uploaded to Google Sheet successfully.")
