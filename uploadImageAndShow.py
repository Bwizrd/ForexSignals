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
    sheets_service = gspread.authorize(creds)
    return drive_service, sheets_service

def upload_image_to_drive(drive_service, file_path):
    """Upload an image to Google Drive and return the file ID."""
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype='image/jpeg')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def update_sheet_with_image(sheets_service, cell_address, image_id):
    """Update a Google Sheet cell with an image link."""
    sheet_id = os.getenv('SHEET_ID')  # Retrieve sheet ID from environment variables
    workbook = sheets_service.open_by_key(sheet_id)
    sheet = workbook.sheet1  # Assuming we're using the first sheet
    image_formula = f'=IMAGE("https://drive.google.com/uc?id={image_id}", 1)'
    sheet.update_acell(cell_address, image_formula)

# Use the functions
drive_service, sheets_service = initialize_google_services()
image_id = upload_image_to_drive(drive_service, 'path/to/your/image.jpg')  # Specify the correct path
update_sheet_with_image(sheets_service, 'A1', image_id)  # Update this cell address as needed

print("Image uploaded and linked in the sheet successfully.")
