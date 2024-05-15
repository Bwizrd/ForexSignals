import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

# Retrieve sensitive information from environment variables


scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)

sheet_id = os.getenv('SHEET_ID')
workbook = client.open_by_key(sheet_id)

# values_list = workbook.sheet1.row_values(1)
# print(values_list)

worksheet_list = map(lambda x: x.title, workbook.worksheets())
print(list(worksheet_list))
# new_worksheet_name = "Values"

sheet_name = "TestSheet1"

try:
    # Attempt to retrieve the worksheet by name
    sheet = workbook.worksheet(sheet_name)
except gspread.WorksheetNotFound:
    # If not found, create a new worksheet with a specified number of rows and columns
    sheet = workbook.add_worksheet(title="TestSheet1", rows="100", cols="20")
    print(f"Worksheet not found. Created new worksheet named {sheet_name}.")

sheet = workbook.worksheet("TestSheet1")
sheet.update_cell(6,1, "Hello World!")
sheet.update_acell("D5", "Hello World!")
value = sheet.acell("F2").value
print(value)

cell = sheet.find("HeartMindCoherence")
print(cell.row, cell.col)

sheet.format("A1:C3", {"textFormat": {"bold": True}})

values = [
    ["Name", "Price", "Quantity"],
    ["Basketball", 29.99, 1],
    ["Jeans", 39.99, 4],
    ["Soap", 7.99, 3],
]

worksheet_list = map(lambda x: x.title, workbook.worksheets())
new_worksheet_name = "Values2"

if new_worksheet_name in worksheet_list:
    sheet = workbook.worksheet(new_worksheet_name)
else:
    sheet = workbook.add_worksheet(new_worksheet_name, rows=10, cols=10)

sheet.clear()

sheet.update(f"A1:C{len(values)}", values)
sheet.format("A1:C1", {"textFormat": {"bold": True}})

sheet.update_cell(len(values) + 1, 2, "=sum(B2:B4)")
sheet.update_cell(len(values) + 1, 3, "=sum(C2:C4)")
