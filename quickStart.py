import cv2

# Print OpenCV version to confirm installation
print("OpenCV version:", cv2.__version__)

# Create a blank image to test OpenCV functionality
image = cv2.imread("dark24.jpg")

if image is not None:
    print("OpenCV can read images.")

    # Display the image in a window
    cv2.imshow("Test Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("Failed to read the image. Check the file path and permissions.")