
import cv2
import numpy as np
from matplotlib import pyplot as plt
import os
import shutil
# from utils.process_white_background import process_white_background
# from utils.process_black_background import process_black_background
from process_white import process_white_background
from process_black import process_black_background
# from utils.display import display_image, display_mask
from display import display_image, display_mask
from image_utils import check_background_color, preprocess_image

display_images = True

image_directory = 'downloaded_images/Landscape'

image_files = [f for f in os.listdir(image_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

# Base folder for classified images
base_folder = 'classified_images'

for image_file in image_files:
    # Get the full path of the image
    image_path = os.path.join(image_directory, image_file)
    base_name = os.path.basename(image_path)
    file_name, _ = os.path.splitext(base_name)

    target_image = cv2.imread(image_path)
    if target_image is None:
        print(f"Error reading image: {image_file}")
        continue  # Skip to the next image if this one cannot be read

    preprocessed_image = preprocess_image(target_image)

    # Check the background color to determine how to process the image
    background = check_background_color(target_image)

    if background == 'Black':
        position = process_black_background(preprocessed_image, target_image)
    else:
        position = process_white_background(preprocessed_image, file_name)

    print(f"Image: {image_file}, Position: {position}")

    # Determine the target folder based on the position
    target_folder = os.path.join(base_folder, position)

    # Ensure the target folder exists
    os.makedirs(target_folder, exist_ok=True)

    # New file path in the target folder
    new_image_path = os.path.join(target_folder, image_file)

    # Move the file to the classified folder
    shutil.move(image_path, new_image_path)

    print(f"Moved {image_file} to: {new_image_path}")