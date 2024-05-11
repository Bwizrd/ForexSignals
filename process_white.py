from contour_utils import find_colors, clean_and_combine_masks, classify_long_short_or_unknown
from display import display_mask
from file_utils import create_save_path, sanitize_filename
import cv2
import numpy as np
import os

def process_white_background(preprocessed_image, file_name):

    target_colors_bgr = [
    [230, 234, 205],  # Light green
    [190, 200, 160],  # Dark green
    [219, 215, 247]   # Red
]

    tolerances = [  # White background
        np.array([20, 20, 20]),  # Tolerance for the first color
        np.array([20, 20, 20]),
        np.array([15, 15, 15])   # Tolerance for the third color
    ]

    masks = find_colors(preprocessed_image, target_colors_bgr, tolerances)

    cleaned_mask_green, cleaned_mask_red = clean_and_combine_masks(masks)
    # Display the cleaned masks
    # display_mask(cleaned_mask_red, 'Red Mask')
    # display_mask(cleaned_mask_green, 'Green Mask')
    contours_red, _ = cv2.findContours(
        cleaned_mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_green, _ = cv2.findContours(
        cleaned_mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    all_contours = contours_red + contours_green
    # Classify as long or short
    position = classify_long_short_or_unknown(
        all_contours, preprocessed_image)

    # Create folder and save image
    save_path = create_save_path("saved_images", position)
    sanitized_filename = sanitize_filename(file_name)

    save_file_path = os.path.join(
        save_path, f"{sanitized_filename}_classified.png")
    cv2.imwrite(save_file_path, preprocessed_image)

    print(f"Image saved as {save_file_path}")

    return position