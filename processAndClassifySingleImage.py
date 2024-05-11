
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

image_path = 'downloaded_images/Landscape/20240416_140042.jpg'
# image_path = 'downloaded_images/Landscape/20240418_192412.jpg'
# image_path = 'downloaded_images/Landscape/20240423_062009.jpg'
base_name = os.path.basename(image_path)
file_name, _ = os.path.splitext(base_name)

target_image = cv2.imread(image_path)
if target_image is None:
    raise ValueError("Invalid image path or unable to read image.")

# display_image(target_image, 'Original Image',
#                   save_image=False, save_path=None, filename=None)
preprocessed_image = preprocess_image(target_image)


# Convert BGR to RGB for displaying in matplotlib
# target_image_rgb = cv2.cvtColor(preprocessed_image, cv2.COLOR_BGR2RGB)

# Display the image in the Jupyter notebook
plt.imshow(target_image)
plt.title(f"Original Image: {file_name}")
plt.axis('off')  # Hide axes for a cleaner display
plt.show()


if display_images:
    display_image(target_image, 'Original Image',
                      save_image=False, save_path=None, filename=None)

background = check_background_color(target_image)


print(background)
if background == 'Black':
    position = process_black_background(preprocessed_image, target_image)
else:
    position = process_white_background(preprocessed_image, file_name)

print(position)


base_folder = 'classified_images'  # Root folder for classified images
target_folder = os.path.join(base_folder, position)  # Folder based on position

# Ensure the target folder exists
os.makedirs(target_folder, exist_ok=True)

# New file path in the target folder
new_image_path = os.path.join(target_folder, base_name)

# Move the file
shutil.move(image_path, new_image_path)

print(f"Moved image to: {new_image_path}")





