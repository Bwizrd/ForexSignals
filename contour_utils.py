import cv2
import numpy as np

def find_colors(image, target_colors, tolerances):
    # Ensure input is in list format for multiple colors
    if not isinstance(target_colors[0], (list, np.ndarray)):
        target_colors = [target_colors]

    # Initialize masks for each color
    masks = []

    for target_color, tolerance in zip(target_colors, tolerances):
        # Convert the target color to a numpy array
        target_color = np.array(target_color, dtype=np.uint8)

        # Calculate the lower and upper bounds of the color range
        lower_bound = target_color - tolerance
        upper_bound = target_color + tolerance

        # Clip the bounds to be within valid color range
        lower_bound = np.clip(lower_bound, 0, 255)
        upper_bound = np.clip(upper_bound, 0, 255)

        # Find the colors within the specified range
        mask = cv2.inRange(image, lower_bound, upper_bound)
        masks.append(mask)

    return masks

# Function to clean and combine masks
def clean_and_combine_masks(masks):
    # Unpack the masks
    mask_green_lighter, mask_green_darker, mask_red = masks

    # Define a kernel for morphological operations
    kernel = np.ones((5, 5), np.uint8)

    # Combine the green masks
    combined_green_mask = cv2.bitwise_or(mask_green_lighter, mask_green_darker)

    # Apply morphological opening and closing to the red mask
    cleaned_mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
    cleaned_mask_red = cv2.morphologyEx(cleaned_mask_red, cv2.MORPH_CLOSE, kernel)

    # Apply morphological opening and closing to the green mask
    cleaned_mask_green = cv2.morphologyEx(combined_green_mask, cv2.MORPH_OPEN, kernel)
    cleaned_mask_green = cv2.morphologyEx(cleaned_mask_green, cv2.MORPH_CLOSE, kernel)

    return cleaned_mask_green, cleaned_mask_red

# Function to approximate and trim contours to remove extremities
def simplify_contour(contour, epsilon=0.02):
    """
    Approximate the contour to remove extremities and smooth it.
    """
    return cv2.approxPolyDP(contour, epsilon * cv2.arcLength(contour, True), True)

def clip_contours_to_right(contours, image_width, right_ratio=0.6):
    clipped_contours = []

    # Define the x-coordinate threshold for the right 60%
    right_threshold = image_width * (1 - right_ratio)

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        # Check if any part of the contour is within the right 60%
        if (x + w) > right_threshold:
            # Clip the contour to the right 60% region
            new_x = max(x, right_threshold)
            new_w = x + w - new_x

            if new_w > 0:
                # Adjust contour points to only include those in the right 60%
                new_contour = [
                    point for point in contour
                    if point[0][0] >= right_threshold
                ]
                clipped_contours.append(np.array(new_contour, dtype=np.int32))

    return clipped_contours

def filter_by_minimum_area(contours, min_area):
    """
    Filters contours based on the minimum area.
    Only keeps contours with an area greater than or equal to the specified minimum area.
    """
    filtered_contours = [
        contour for contour in contours if cv2.contourArea(contour) >= min_area]
    return filtered_contours

def filter_by_edge_count(contours, max_edges=20):
    filtered_contours = []
    for contour in contours:
        # Approximate the contour to a polygon
        # Adjust epsilon as needed
        epsilon = 0.01 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        # print("Number of edges:", len(approx))

        # If the number of edges is less than or equal to the threshold, keep it
        if len(approx) <= max_edges:
            filtered_contours.append(contour)
    return filtered_contours

def filter_rectangular_contours(contours_with_corners, minimum_fill_ratio=0.7):
    valid_contours = []

    # Sort contours by their top-left corner's x-coordinate to detect nesting
    contours_with_corners = sorted(contours_with_corners, key=lambda c: c['top_left'][0])

    # Initialize a list to track whether each contour is nested
    nested_info = []  # Store nested status and other info for each contour

    for i, outer_contour_data in enumerate(contours_with_corners):
        is_nested = False
        top_left = outer_contour_data['top_left']
        bottom_right = outer_contour_data['bottom_right']

        # Calculate the rectangle area
        rect_width = bottom_right[0] - top_left[0]
        rect_height = bottom_right[1] - top_left[1]
        rectangle_area = rect_width * rect_height

        outer_contour = outer_contour_data['contour']
        outer_contour_area = cv2.contourArea(outer_contour)
        # outer_contour_approx = approximate_contour(outer_contour)

        # outer_contour_area = cv2.contourArea(outer_contour_approx)

        # Check if this contour encompasses another (is nested)
        for inner_contour_data in contours_with_corners:
            if inner_contour_data['contour_number'] != outer_contour_data['contour_number']:
                inner_top_left = inner_contour_data['top_left']
                inner_bottom_right = inner_contour_data['bottom_right']

                if (inner_top_left[0] >= top_left[0] and
                    inner_top_left[1] >= top_left[1] and
                    inner_bottom_right[0] <= bottom_right[0] and
                    inner_bottom_right[1] <= bottom_right[1]):
                    
                    # Add the inner contour's area to the outer contour's area
                    inner_area = cv2.contourArea(inner_contour_data['contour'])
                    outer_contour_area += inner_area
                    is_nested = True
                    break  # No need to check further if nesting is detected

        # Calculate the fill ratio with nested areas
        fill_ratio = outer_contour_area / rectangle_area

        # Check the fill ratio and add to valid contours if it meets the threshold
        if fill_ratio >= minimum_fill_ratio:
            valid_contours.append(outer_contour_data)

        # Store contour information with the calculated fill ratio and nested status
        nested_info.append({
            'contour_number': outer_contour_data['contour_number'],
            'rectangle_area': rectangle_area,
            'outer_contour_area': outer_contour_area,
            'fill_ratio': fill_ratio,
            'is_nested': is_nested
        })

    # Display the nested information in a table format
    print("Contour | Rectangle Area | Outer Contour Area | Fill Ratio | Nested")
    print("----------------------------------------------------------")
    for info in nested_info:
        print(
            f"{info['contour_number']}     | "
            f"{info['rectangle_area']}     | "
            f"{info['outer_contour_area']}     | "
            f"{info['fill_ratio']:.2f}     | "
            f"{'Yes' if info['is_nested'] else 'No'}"
        )

    return valid_contours
# Define a function to check if a contour is valid
def is_valid_contour(contour):
    # A valid contour must have at least three points
    return isinstance(contour, np.ndarray) and contour.ndim == 3 and contour.shape[1] == 1 and contour.shape[2] == 2

def find_most_rectangular(contours):
    most_rectangular_contour = None
    most_rectangular_score = float('inf')  # Initialize with a high value
    most_rectangular_contour_number = None

    # Loop through contours to find the most rectangular
    for i, contour in enumerate(contours):
        if is_valid_contour(contour):
            # Get the bounding rectangle
            x, y, width, height = cv2.boundingRect(contour)

            # Extract the top-left and bottom-left corners
            top_left = (x, y)
            bottom_left = (x, y + height)

            # Calculate the horizontal distance between these points
            horizontal_distance = abs(top_left[0] - bottom_left[0])

            # Compute a score based on the height-to-width ratio and horizontal distance
            rectangularity_score = horizontal_distance / width  # Closer to 0 is better

            # Ensure the contour has a significant width-to-height ratio
            if width >= 500 and height > 0 and width > height:
                if rectangularity_score < most_rectangular_score:
                    most_rectangular_score = rectangularity_score
                    most_rectangular_contour = contour
                    most_rectangular_contour_number = i + 1  # Keep track of contour number

    return most_rectangular_contour_number

def match_contour_pairs(contours_with_centers, x_distance_threshold=10, width_tolerance=20):
    """
    Find pairs of contours with centers that are close on the X-axis
    and have similar widths.
    """
    matched_pairs = []  # To store matched pairs of contours

    # Loop through all contour combinations
    for i in range(len(contours_with_centers)):
        for j in range(i + 1, len(contours_with_centers)):
            # Get the center points and widths of the two contours
            contour1 = contours_with_centers[i]
            contour2 = contours_with_centers[j]

            x_distance = abs(contour1["leftmost_x"] - contour2["leftmost_x"])

            # Check the difference in widths
            width_difference = abs(contour1["width"] - contour2["width"])

            # print(f"Contour {i+1} & {j+1} - X Distance: {x_distance}, Width Difference: {width_difference}")

            # If the distance and width are within the specified thresholds
            if x_distance <= x_distance_threshold and width_difference <= width_tolerance:
                # Add the pair to the list of matched pairs
                matched_pairs.append((contour1, contour2))

    return matched_pairs  # Return the list of matched pairs

def find_similar_width_and_aligned_edges(matched_pairs, width_tolerance=20, x_axis_tolerance=10):
    aligned_contours = []

    for contour_pair in matched_pairs:
        contour1 = contour_pair[0]['contour']
        contour2 = contour_pair[1]['contour']

        # Get bounding rectangles for the contours
        x1, y1, w1, h1 = cv2.boundingRect(contour1)
        x2, y2, w2, h2 = cv2.boundingRect(contour2)

        # Calculate the difference in widths
        width_difference = abs(w1 - w2)

        # Check if the left edges are aligned within tolerance
        left_edge_difference = abs(x1 - x2)

        # Check if the right edges are aligned within tolerance
        right_edge_difference = abs((x1 + w1) - (x2 + w2))

        # If width difference and edge alignment are within tolerances
        if (width_difference <= width_tolerance and 
            left_edge_difference <= x_axis_tolerance and
            right_edge_difference <= x_axis_tolerance):
            aligned_contours.append((contour_pair[0], contour_pair[1]))  # Add to aligned pairs

    return aligned_contours

def classify_long_short_or_unknown(contours, image):
    red_contours = []
    green_contours = []

    # Adjust tolerance for considering red or green dominance
    color_threshold = 20  # Adjust as needed
    
    for contour in contours:
        # Create a mask to get the mean color of the contour
        mask = np.zeros_like(image[:, :, 0], dtype=np.uint8)  # Only need 1 channel for the mask
        cv2.drawContours(mask, [contour], -1, 255, -1)
        
        # Compute the mean color
        mean_color = cv2.mean(image, mask=mask)
        
        # Consider pixels only above a certain brightness level to avoid black influences
        if mean_color[2] > mean_color[1] + color_threshold:
            red_contours.append(contour)
        elif mean_color[1] > mean_color[2] + color_threshold:
            green_contours.append(contour)
    
    # Validate that there are at least one red and one green contour
    if not red_contours or not green_contours:
        return "unknown"

    # Determine the topmost position for red and green contours
    red_topmost = min(cv2.boundingRect(c)[1] for c in red_contours)
    green_topmost = min(cv2.boundingRect(c)[1] for c in green_contours)
    
    # Classify based on the vertical position
    if red_topmost < green_topmost:
        return "short"
    elif green_topmost < red_topmost:
        return "long"
    
    return "unknown"