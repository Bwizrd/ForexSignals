import cv2
import numpy as np

def preprocess_image(image):

    # Apply Gaussian blur to reduce noise
    blurred_image = cv2.GaussianBlur(image, (5, 5), 0)

    # Apply morphological operations to clean the image
    kernel = np.ones((3, 3), np.uint8)  # Adjust kernel size as needed
    opened_image = cv2.morphologyEx(blurred_image, cv2.MORPH_OPEN, kernel)  # Erosion followed by dilation

    return opened_image

def classify_aspect_ratio(width, height):
    aspect_ratio = width / height
    
    # Define aspect ratio categories
    if aspect_ratio > 1.1:
        return "Landscape"  # Wider than tall
    elif aspect_ratio < 0.9:
        return "Portrait"  # Taller than wide
    else:
        return "Square"  # Approximately equal width and height
    

def check_background_color(image):
    # Flatten the image into a single array of pixels
    flattened_pixels = image.reshape((-1, 3))

    # Calculate the mean color across the image
    mean_color = np.mean(flattened_pixels, axis=0)

    # Set a threshold to distinguish between black and white
    threshold = 127  # The midpoint for 8-bit colors

    # Determine if the mean color is predominantly black or white
    if np.all(mean_color < threshold):
        return "Black"
    elif np.all(mean_color > threshold):
        return "White"
    else:
        return "Mixed"