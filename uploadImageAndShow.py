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

def upload_image_to_drive(drive_service, file_path):
    """Upload an image to Google Drive and return the file ID with public access."""
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype='image/jpeg')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')
    # Set the file to be accessible by anyone with the link
    permission = {'type': 'anyone', 'role': 'reader'}
    drive_service.permissions().create(fileId=file_id, body=permission).execute()
    return file_id

def adjust_cell_size(sheets_service, spreadsheet_id, sheet_id, start_row, start_col, height, width):
    """Adjust the cell size to specified height and width using Google Sheets API."""
    requests = [
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": start_row - 1, 
                    "endIndex": start_row
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
                    "startIndex": start_col - 1,
                    "endIndex": start_col
                },
                "properties": {
                    "pixelSize": width
                },
                "fields": "pixelSize"
            }
        }
    ]
    body = {"requests": requests}
    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

def update_sheet_with_image_and_link(sheets_service, gspread_client, spreadsheet_id, sheet_id, start_row, start_col, image_id, image_height, image_width):
    """Update a Google Sheet cell with an image and adjust cell size."""
    workbook = gspread_client.open_by_key(spreadsheet_id)
    sheet = workbook.worksheet('Sheet4')  # Assuming 'Sheet4' is the target sheet
    # image_formula = f'=IMAGE("https://drive.google.com/uc?id={image_id}", 4, {image_height}, {image_width})'
    image_formula = f'=IMAGE("https://drive.google.com/uc?id={image_id}", 1)'
    hyperlink_formula = f'=HYPERLINK("https://drive.google.com/uc?id={image_id}", "Open Image")'
    # Update cell with image
    sheet.update_acell(f'A{start_row}', image_formula)
    # Update cell below with hyperlink
    sheet.update_acell(f'A{start_row + 1}', hyperlink_formula)
    # Adjust cell sizes
    adjust_cell_size(sheets_service, spreadsheet_id, sheet_id, start_row, start_col, image_height, image_width)

# Use the functions
drive_service, sheets_service, gspread_client = initialize_google_services()
image_id = upload_image_to_drive(drive_service, 'downloaded_images/20240515_104616.jpg')
spreadsheet_id = os.getenv('SHEET_ID')
workbook = gspread_client.open_by_key(spreadsheet_id)
sheet = workbook.worksheet('Sheet4')
sheet_id = sheet.id  # Get the numeric sheet ID for the API calls
update_sheet_with_image_and_link(sheets_service, gspread_client, spreadsheet_id, sheet_id, 2, 1, image_id, 300, 500)

print("Image uploaded and linked in the sheet successfully.")
