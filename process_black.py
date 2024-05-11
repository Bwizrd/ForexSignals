import cv2
import numpy as np
from display import display_mask, display_image
from contour_utils import clip_contours_to_right, filter_by_edge_count, filter_by_minimum_area, simplify_contour, filter_rectangular_contours
from contour_utils import find_most_rectangular, match_contour_pairs, find_similar_width_and_aligned_edges, classify_long_short_or_unknown
from drawing import draw_rectangles, draw_filtered_rectangles

display_images = False

def process_black_background(preprocessed_image, target_image):
    hsv_image = cv2.cvtColor(preprocessed_image, cv2.COLOR_BGR2HSV)

    # Define HSV color ranges for green and red
    # Adjust the lower and upper bounds as needed to capture the colors accurately
    green_lower = np.array([35, 50, 50])  # Lower bound for green
    green_upper = np.array([95, 255, 255])  # Upper bound for green
    red_lower1 = np.array([0, 50, 50])  # Lower bound for red
    red_upper1 = np.array([5, 255, 255])  # Upper bound for red
    # Lower bound for red (for reds near 0)
    red_lower2 = np.array([170, 50, 50])
    # Upper bound for red (for reds near 180)
    red_upper2 = np.array([175, 255, 255])

    # Create masks for green and red
    mask_green = cv2.inRange(hsv_image, green_lower, green_upper)
    mask_red1 = cv2.inRange(hsv_image, red_lower1, red_upper1)
    mask_red2 = cv2.inRange(hsv_image, red_lower2, red_upper2)

    # Combine the red masks to get all red regions
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    kernel = np.ones((5, 5), np.uint8)
    cleaned_mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
    cleaned_mask_red = cv2.morphologyEx(
        cleaned_mask_red, cv2.MORPH_CLOSE, kernel)
    cleaned_mask_green = cv2.morphologyEx(
        mask_green, cv2.MORPH_OPEN, kernel)
    cleaned_mask_green = cv2.morphologyEx(
        cleaned_mask_green, cv2.MORPH_CLOSE, kernel)
    if display_images:
        display_mask(mask_red, 'Red Mask')
        display_mask(mask_green, 'Green Mask')
    contours_red, _ = cv2.findContours(
        cleaned_mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_green, _ = cv2.findContours(
        cleaned_mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # List to store contour information
    contour_data = []

    # Loop through red contours to get bounding rectangles and the number of edges
    for contour in contours_red:
        x, y, w, h = cv2.boundingRect(contour)
        # Approximate contour to find the number of edges
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        contour_data.append({
            'color': 'Red',
            'x': x,
            'y': y,
            'width': w,
            'height': h,
            'num_edges': len(approx)
        })

    # Loop through green contours to get bounding rectangles and the number of edges
    for contour in contours_green:
        x, y, w, h = cv2.boundingRect(contour)
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        contour_data.append({
            'color': 'Green',
            'x': x,
            'y': y,
            'width': w,
            'height': h,
            'num_edges': len(approx)
        })

    # Print out the contour data in a table
    # print("Color | X | Y | Width | Height | Num. Edges")
    # print("-------------------------------------------")
    # for data in contour_data:
    #     print(f"{data['color']}  | {data['x']}  | {data['y']}  | {data['width']}  | {data['height']}  | {data['num_edges']}")

    temp_image = np.zeros_like(target_image)

    # Draw all red contours
    cv2.drawContours(temp_image, contours_red, -1, (255, 0, 0), 2)

    # Draw all green contours
    cv2.drawContours(temp_image, contours_green, -1, (0, 255, 0), 2)

    # Display the visualization
    # display_image(temp_image, "All Contours Before Filtering", save_image=False, save_path=None, filename=None)

    image_width = target_image.shape[1]

    # Define the right-side threshold (last 5% of the image width)
    right_threshold = image_width * 0.95  # 95% of the image width

    # Filter out contours located in the last 5% on the right
    filtered_contours_red = [
        contour for contour in contours_red
        if cv2.boundingRect(contour)[0] < right_threshold
    ]

    filtered_contours_green = [
        contour for contour in contours_green
        if cv2.boundingRect(contour)[0] < right_threshold
    ]

    image_height = target_image.shape[0]
    top_threshold = image_height * 0.1  # 5% of the image height

    # Filter out contours located in the top 5%
    filtered_contours_red = [
        contour for contour in filtered_contours_red
        if cv2.boundingRect(contour)[1] > top_threshold
    ]

    filtered_contours_green = [
        contour for contour in filtered_contours_green
        if cv2.boundingRect(contour)[1] > top_threshold
    ]

    max_width_threshold = 500

    # Apply the width filter to red contours
    filtered_contours_red = [
        contour for contour in filtered_contours_red
        if cv2.boundingRect(contour)[1] > top_threshold
        and cv2.boundingRect(contour)[2] <= max_width_threshold  # Width check
    ]

    # Apply the width filter to green contours
    filtered_contours_green = [
        contour for contour in filtered_contours_green
        if cv2.boundingRect(contour)[1] > top_threshold
        and cv2.boundingRect(contour)[2] <= max_width_threshold  # Width check
    ]

    filtered_contours_red = clip_contours_to_right(
        filtered_contours_red, image_width, right_ratio=0.6)
    filtered_contours_green = clip_contours_to_right(
        filtered_contours_green, image_width, right_ratio=0.6)


    filtered_contours_red = filter_by_edge_count(
        filtered_contours_red, max_edges=20)
    filtered_contours_green = filter_by_edge_count(
        filtered_contours_green, max_edges=20)

    min_area = 50  # Adjust this value as needed
    filtered_contours_red = filter_by_minimum_area(
        filtered_contours_red, min_area)
    filtered_contours_green = filter_by_minimum_area(
        filtered_contours_green, min_area)

    combined_contour_image = np.zeros_like(target_image)
    cv2.drawContours(combined_contour_image,
                        filtered_contours_red, -1, (0, 0, 255), 1)

    # Draw green contours
    cv2.drawContours(combined_contour_image,
                        filtered_contours_green, -1, (0, 255, 0), 1)

    # Display the combined contour image
    # display_image(combined_contour_image, 'Combined Red and Green Contours',
    #                 save_image=False, save_path=None, filename=None)
    # Combine red and green contours for processing

    all_contours = filtered_contours_red + filtered_contours_green
    simplified_contours = [simplify_contour(contour) for contour in all_contours]

    # List to store contour information with centers and additional data
    contours_with_centers = []

    # Loop through each contour with its index
    for index, contour in enumerate(simplified_contours):
        # Get the bounding rectangle for the contour
        x, y, w, h = cv2.boundingRect(contour)

        top_left = (x, y)
        top_right = (x + w, y)
        bottom_left = (x, y + h)
        bottom_right = (x + w, y + h)

        contour_area = cv2.contourArea(contour)

        # The uppermost horizontal edge's center point (x-coordinate)
        uppermost_horizontal_center_x = x + (w / 2)

        # The y-coordinate of the top edge (uppermost horizontal edge)
        top_edge_y = y

        # Calculate the width
        contour_width = w

        leftmost_x = x

        # Add the calculated data to the list with the contour number
        contours_with_centers.append({
            "contour": contour,
            "contour_number": index + 1,  # Numbering starting from 1
            "center_x": uppermost_horizontal_center_x,
            "top_edge_y": y,
            "width": contour_width,
            "leftmost_x": leftmost_x,
            "top_left": top_left,
            "top_right": top_right,
            "bottom_left": bottom_left,
            "bottom_right": bottom_right,
            "area": contour_area
        })

    # Display the results in a simple tabular format
    print("Contour | Center X | Top Edge Y | Width | Leftmost X | Top Left | Top Right | Bottom Left | Bottom Right | Area")
    print("---------------------------------------")
    for contour_data in contours_with_centers:
        top_left = contour_data['top_left']
        top_right = contour_data['top_right']
        bottom_left = contour_data['bottom_left']
        bottom_right = contour_data['bottom_right']
        print(
            f"{contour_data['contour_number']}     | "
            f"{contour_data['center_x']:.2f}     | "
            f"{contour_data['top_edge_y']}     | "
            f"{contour_data['width']:.2f}    |" 
            f"{contour_data['leftmost_x']:.2f}     | "
            f"{top_left}     | "
            f"{top_right}     | "
            f"{bottom_left}     | "
            f"{contour_data['bottom_right']}     | "
            f"{contour_data['area']:.2f}"
        )

    # Create a new image to draw contours on
    image_with_contour_numbers = np.zeros_like(target_image)

    # Draw the contours on the new image
    cv2.drawContours(
        image_with_contour_numbers,
        [data['contour'] for data in contours_with_centers],  # Extract the contours from the dictionary
        -1,
        (255, 255, 255),  # White color for the contours
        2
    )

    # Loop through the contours and add text with the contour number and center point
    for contour_data in contours_with_centers:
        contour_number = contour_data["contour_number"]
        center_x = contour_data["center_x"]
        top_edge_y = contour_data["top_edge_y"]

        # Draw the contour number text at the uppermost horizontal edge
        text_position = (int(center_x), int(top_edge_y - 10))  # Slightly above the edge
        cv2.putText(
            image_with_contour_numbers,
            f"{contour_number}",
            text_position,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),  # Green text
            2,
        )
        # print('Contour Numbers')
        # print("Contour | Center X | Top Edge Y | Width")
        # print(
        #     f"{contour_data['contour_number']}     | "
        #     f"{contour_data['center_x']:.2f}     | "
        #     f"{contour_data['top_edge_y']}     | "
        #     f"{contour_data['width']:.2f}"
        # )

    # Display the image with contour numbers
    # display_image(
    #     image_with_contour_numbers,
    #     'Contour Numbers',
    #     save_image=False,  # Set to True to save the image
    #     save_path=None,  # Provide a save path if needed
    #     filename=None  # Provide a filename if saving
    # )

    # Example code to draw valid rectangles
    image_with_rectangles = draw_rectangles(target_image, contours_with_centers)
    # valid_contours_with_corners = remove_nested_rectangles(valid_contours_with_corners)
    valid_contours_with_corners = filter_rectangular_contours(contours_with_centers, minimum_fill_ratio=0.5)
    image_with_filtered_rectangles = draw_filtered_rectangles(target_image, valid_contours_with_corners)
    # Display the updated image
    if display_images:
        display_image(image_with_rectangles, 'Validated Rectangles')
        display_image(image_with_filtered_rectangles, 'Valid Filtered Rectangles')

    # Display the contour number for the most rectangular contour
    print("Most Rectangular Contour Number:", find_most_rectangular(valid_contours_with_corners))

    if len(valid_contours_with_corners) == 2:
        # If there are only two contours, they are the matched pair
        matched_pairs = [(valid_contours_with_corners[0], valid_contours_with_corners[1])]
    else:
        # If there are more than two, use the matching function
        matched_pairs = match_contour_pairs(
            valid_contours_with_corners, x_distance_threshold=15, width_tolerance=100
        )

    # Find matched contour pairs
    # matched_pairs = match_contour_pairs(contours_with_centers, x_distance_threshold=15, width_tolerance=100)
    # print("Matched pairs:", matched_pairs)

    # Create an image to draw contours
    # Get the contours directly from contours_with_centers
    # all_contours = [data['contour'] for data in contours_with_centers]

    # Function to get contour by contour number from contours_with_centers
    def get_contour_by_number(contour_number, contours_with_centers):
        return contours_with_centers[contour_number - 1]['contour']

    aligned_contours = find_similar_width_and_aligned_edges(matched_pairs, width_tolerance=50, x_axis_tolerance=50)
    final_contours_image = np.zeros_like(target_image)
    
    if aligned_contours:
        print("Aligned Contours:")
        for contour1, contour2 in aligned_contours:
            contour1_number = contour1['contour_number']
            contour2_number = contour2['contour_number']
            print(f"Contour {contour1_number} is aligned with Contour {contour2_number}")

        # Visualize the aligned contours
        aligned_contours_image = np.zeros_like(final_contours_image)
        for contour1, contour2 in aligned_contours:
            cv2.drawContours(aligned_contours_image, [contour1['contour']], -1, (255, 0, 0), 3)  # Red
            cv2.drawContours(aligned_contours_image, [contour2['contour']], -1, (0, 255, 0), 3)  # Green
        if display_images:
            display_image(
                aligned_contours_image,
                'Aligned Contours',
                save_image=False,
                save_path=None,
                filename=None
            )
    else:
        print("No aligned contours found.")
    # Create a new image to draw the matched pairs on
    image_with_matched_pairs = np.zeros_like(target_image)  # Use a similar size to the target image

    # Loop through the matched pairs and draw the contours
    for pair in aligned_contours:
        # Get the contours from the pair
        contour1 = get_contour_by_number(pair[0]['contour_number'], contours_with_centers)
        contour2 = get_contour_by_number(pair[1]['contour_number'], contours_with_centers)

        # Determine which contour is higher on the Y-axis
        if pair[0]["top_edge_y"] < pair[1]["top_edge_y"]:
            higher_contour = contour1
            lower_contour = contour2
        else:
            higher_contour = contour2
            lower_contour = contour1

        # Draw the higher contour in green
        cv2.drawContours(image_with_matched_pairs, [higher_contour], -1, (0, 255, 0), 2)  # Green
        
        # Draw the lower contour in red
        cv2.drawContours(image_with_matched_pairs, [lower_contour], -1, (255, 0, 0), 2)  # Red
        
        # Add contour numbers to the image
        cv2.putText(
            image_with_matched_pairs,
            f"{pair[0]['contour_number']}",
            (int(pair[0]['center_x']), int(pair[0]['top_edge_y'] - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        
        cv2.putText(
            image_with_matched_pairs,
            f"{pair[1]['contour_number']}",
            (int(pair[1]['center_x']), int(pair[1]['top_edge_y'] - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

    # Display the image with matched pairs and their contour numbers
    if display_images:
        display_image(
            image_with_matched_pairs,
            'Matched Contours',
            save_image=False,
            save_path=None,
            filename=None,
        )

    # Create a new image to draw the final contours
    final_contours_image = np.zeros_like(target_image)

    # Draw the filtered contours with appropriate colors
    for index, contour_pair in enumerate(aligned_contours):
        # Determine which contour is higher on the Y-axis
        if contour_pair[0]['top_edge_y'] < contour_pair[1]['top_edge_y']:
            lower_contour = contour_pair[0]['contour']
            higher_contour = contour_pair[1]['contour']
        else:
            lower_contour = contour_pair[1]['contour']
            higher_contour = contour_pair[0]['contour']

        # Draw the lower contour in red
        cv2.drawContours(final_contours_image, [lower_contour], -1, (255, 0, 0), 3)  # Red

        # Draw the higher contour in green
        cv2.drawContours(final_contours_image, [higher_contour], -1, (0, 255, 0), 3)  # Green

    # Display the final contours image
    if display_images:
        display_image(
            final_contours_image,
            'Final Contours',
            save_image=False,  # Set to True to save the image
            save_path=None,
            filename=None,
        )

    contour_areas = [(cv2.contourArea(contour_data['contour']), contour_data) for contour_pair in aligned_contours for contour_data in contour_pair]

    if contour_areas:
        # Sort the list by area in descending order
        contour_areas_sorted = sorted(contour_areas, key=lambda x: x[0], reverse=True)

        # Select the top two contours based on area
        top_two_contours = [data[1] for data in contour_areas_sorted[:2]]

        matched_pairs = [(top_two_contours[0], top_two_contours[1])]

    else:
        # If no contour areas, matched_pairs is empty, and we need to initialize the output variable
        matched_pairs = []
        top_two_contours = []

    shaded_contours_image = np.zeros_like(target_image)
    if matched_pairs:
        # Draw and fill the contours with their original colors on the black background
        for contour_pair in matched_pairs:
            # Draw each contour in the pair
            for contour_data in contour_pair:
                contour = contour_data['contour']
                
                # Create a mask for the current contour
                contour_mask = np.zeros_like(mask_red)
                cv2.drawContours(contour_mask, [contour], -1, 255, -1)

                # Compute the mean color of the contour area in the original image
                mean_val = cv2.mean(target_image, mask=contour_mask)
                mean_color = (int(mean_val[0]), int(mean_val[1]), int(mean_val[2]))

                # Fill the contour with the mean color on the black background image
                cv2.drawContours(shaded_contours_image, [contour], -1, mean_color, cv2.FILLED)

        # Display the shaded contours image with black background
        if display_images:
            display_image(
                shaded_contours_image,
                'Shaded Contours with Black Background',
                save_image=False,  # Set to True to save the image
                save_path='test_images',
                filename='Test24b'
            )

    if matched_pairs:
        desired_contours = [contour_data['contour'] for pair in matched_pairs for contour_data in pair]
        position = classify_long_short_or_unknown(desired_contours, shaded_contours_image)
    else:
        # Handle the case where there are no matched pairs
        desired_contours = []
        position = 'No Matched Pairs'

    desired_contours = [contour_data['contour'] for pair in matched_pairs for contour_data in pair]

    # Classify whether it's long or short using these contours and the shaded image with the black background
    print(position)
    return position