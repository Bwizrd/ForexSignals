import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import gspread
from dotenv import load_dotenv

def initialize_google_services():
    """Initialize Google Drive and Sheets services."""
    load_dotenv()  # Load environment variables from .env file
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
    drive_service = build('drive', 'v3', credentials=creds)
    gspread_client = gspread.authorize(creds)  # For using gspread functions
    sheets_service = build('sheets', 'v4', credentials=creds)  # For direct API calls
    return drive_service, sheets_service, gspread_client

def adjust_cell_size(sheets_service, spreadsheet_id, sheet_id, height, width):
    """Adjust the cell size of A1 to specified height and width using Google Sheets API."""
    requests = [
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": 0,  # A1 row index
                    "endIndex": 1    # Exclusive, so 1 means it only affects the first row
                },
                "properties": {
                    "pixelSize": height
                },
                "fields": "pixelSize"
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,  # A1 column index
                    "endIndex": 1    # Exclusive, so 1 means it only affects the first column
                },
                "properties": {
                    "pixelSize": width
                },
                "fields": "pixelSize"
            }
        }
    ]
    body = {"requests": requests}
    response = sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    return response

# Use the functions
drive_service, sheets_service, gspread_client = initialize_google_services()
spreadsheet_id = os.getenv('SHEET_ID')  # This should be the ID of the spreadsheet, not sheet
workbook = gspread_client.open_by_key(spreadsheet_id)
sheet = workbook.worksheet('Sheet4')
sheet_id = sheet.id  # Get the correct numeric sheet ID for API calls
adjust_cell_size(sheets_service, spreadsheet_id, sheet_id, 500, 500)  # Set A1 to 500x500 pixels

print("Cell A1 size adjusted to 500x500 pixels successfully.")
