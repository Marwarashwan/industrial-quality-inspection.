import cv2
import numpy as np
import os

def inspect_part(image_path):
    # Resolve absolute path relative to project root
    if not os.path.exists(image_path):
        print(f"Error: Could not find file at '{os.path.abspath(image_path)}'")
        return

    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Unable to decode image at '{image_path}'")
        return

    # Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Detect contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Inspection Run: Detected {len(contours)} contours/features.")

    # Annotate detected contours with green outline
    cv2.drawContours(img, contours, -1, (0, 255, 0), 2)

    # Output directory handling
    output_dir = os.path.dirname(image_path)
    output_path = os.path.join(output_dir, "output_result.png")
    cv2.imwrite(output_path, img)
    print(f"Success! Processed image saved to '{output_path}'.")

if __name__ == "__main__":
    # Point directly to your test image location
    inspect_part("src/Sample_testing/copy.jpg")