import cv2
import numpy as np

def is_right_angle(v1, v2, tolerance=0.1):
    dot_product = np.dot(v1, v2)
    return np.isclose(dot_product, 0, atol=tolerance)

def is_rectangle(top_left, top_right, bottom_left, bottom_right):
    # Calculate the vectors for each side
    vector_top = np.array(top_right) - np.array(top_left)
    vector_bottom = np.array(bottom_right) - np.array(bottom_left)
    vector_left = np.array(bottom_left) - np.array(top_left)
    vector_right = np.array(bottom_right) - np.array(top_right)
    
    # Calculate the distances (lengths of the sides)
    length_top = np.linalg.norm(vector_top)
    length_bottom = np.linalg.norm(vector_bottom)
    length_left = np.linalg.norm(vector_left)
    length_right = np.linalg.norm(vector_right)

    # Check if opposite sides are roughly equal in length
    opposite_sides_equal = (
        np.isclose(length_top, length_bottom, atol=5) and
        np.isclose(length_left, length_right, atol=5)
    )
    
    # Check if adjacent sides are perpendicular
    perpendicular_sides = (
        is_right_angle(vector_top, vector_left) and
        is_right_angle(vector_left, vector_bottom) and
        is_right_angle(vector_bottom, vector_right)
    )
    
    return opposite_sides_equal and perpendicular_sides

def draw_rectangles(image, contours_with_corners):
    rectangle_image = image.copy()

    font_scale = 1.5  # Increase this for a larger font size
    font_thickness = 2
    contour_info = []

    # Label contours with their number and check for nested rectangles
    for contour_data in contours_with_corners:
        contour_number = contour_data["contour_number"]

        # Get the corners
        top_left = contour_data['top_left']
        top_right = contour_data['top_right']
        bottom_left = contour_data['bottom_left']
        bottom_right = contour_data['bottom_right']

        # Check if it's a valid rectangle by using all four corners
        if is_rectangle(top_left, top_right, bottom_left, bottom_right):
            # Draw the rectangle
            cv2.rectangle(
                rectangle_image,
                tuple(top_left),
                tuple(bottom_right),
                (0, 255, 0),  # Green color for valid rectangles
                2
            )

            # Add contour number as a label
            label_position = (top_left[0], top_left[1] - 10)  # Slightly above the top-left corner
            cv2.putText(
                rectangle_image,
                f"{contour_number}",
                label_position,
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,  # Use the updated font scale
                (0, 255, 0),  # Green text
                font_thickness  # Use the updated font thickness
            )
        else:
            # Mark with a different color for invalid rectangles
            cv2.rectangle(
                rectangle_image,
                tuple(top_left),
                tuple(bottom_right),
                (255, 0, 0),  # Red color for invalid rectangles
                font_thickness
            )

        # Check for nested rectangles
        is_nested = any(
            other_contour_data['contour_number'] != contour_number and
            other_contour_data['top_left'][0] >= top_left[0] and
            other_contour_data['top_left'][1] >= top_left[1] and
            other_contour_data['bottom_right'][0] <= bottom_right[0] and
            other_contour_data['bottom_right'][1] <= bottom_right[1]
            for other_contour_data in contours_with_corners
        )

        # Label nested rectangles
        if is_nested:
            nested_label_position = (top_left[0], top_left[1] - 25)  # Higher to indicate nesting
            cv2.putText(
                rectangle_image,
                f"{contour_number} (Nested)",
                nested_label_position,
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),  # White text for nested labels
                font_thickness
            )
        # Store contour information for debugging
        contour_info.append({
            'contour_number': contour_number,
            'is_nested': is_nested,
            'top_left': top_left,
            'bottom_right': bottom_right,
        })
    
    # Display contour information in a table format
    print("Contour | Top Left | Bottom Right | Nested")
    print("------------------------------------------")
    for info in contour_info:
        print(
            f"{info['contour_number']}     | "
            f"{info['top_left']}     | "
            f"{info['bottom_right']}     | "
            f"{'Yes' if info['is_nested'] else 'No'}"
        )
    
    return rectangle_image

# Function to draw rectangles based on the filtered contours
def draw_filtered_rectangles(image, contours_with_corners):
    filtered_image = image.copy()

    for contour_data in contours_with_corners:
        top_left = contour_data['top_left']
        bottom_right = contour_data['bottom_right']
        
        # Draw the rectangles for valid contours
        cv2.rectangle(
            filtered_image,
            tuple(top_left),
            tuple(bottom_right),
            (0, 255, 0),  # Green color for valid rectangles
            2
        )
    
    return filtered_image