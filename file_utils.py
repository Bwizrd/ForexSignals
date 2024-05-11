import os
import string
import cv2
import shutil
from image_utils import classify_aspect_ratio

def sanitize_filename(filename):
    """ Sanitize a string to be safe for filenames. """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars).strip()

def ensure_directory(path):
    """ Ensure the specified directory exists, creating it if necessary. """
    if not os.path.exists(path):
        os.makedirs(path)
        
# Create a save path and ensure the directory exists
def create_save_path(base_path, subfolder):
    # Join the base path with the subfolder
    full_path = os.path.join(base_path, subfolder)
    
    # If the directory doesn't exist, create it
    if not os.path.exists(full_path):
        os.makedirs(full_path)
        
    return full_path

def move_files_by_aspect():
    # Folder containing the image files
    folder_path = 'downloaded_images'

    # Loop through all image files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            # Read the image
            image_path = os.path.join(folder_path, filename)
            image = cv2.imread(image_path)
            
            # Get image dimensions
            height, width, _ = image.shape
            
            # Classify aspect ratio
            aspect_class = classify_aspect_ratio(width, height)
            
            # Define the destination folder based on aspect ratio classification
            destination_folder = os.path.join(folder_path, aspect_class)
            
            # Create the subfolder if it doesn't exist
            os.makedirs(destination_folder, exist_ok=True)
            
            # Define the new path for the image
            new_image_path = os.path.join(destination_folder, filename)
            
            # Move the image to the appropriate folder
            shutil.move(image_path, new_image_path)
            
            # Output the movement result
            print(f"Moved {filename} to {new_image_path}")