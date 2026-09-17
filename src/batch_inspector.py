import cv2
import numpy as np

def classify_gear(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0 or area < 500: # Filter out small noise
            continue 

        # Metric 1: Circularity Score (1.0 = Perfect Circle)
        circularity = (4 * np.pi * area) / (perimeter ** 2)
        
        # Metric 2: Convex Hull Ratio (Detects depth of teeth cutouts)
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0

        # Simple Classification Rules
        if solidity < 0.75:
            gear_type = "Spur / External Gear (Deep Teeth)"
        elif circularity > 0.85:
            gear_type = "Smooth Bearing / Shaft Collar"
        else:
            gear_type = "Internal / Special Profile Gear"

        print(f"Detected Object: {gear_type} | Solidity: {solidity:.2f} | Circularity: {circularity:.2f}")

classify_gear("src/Sample_testing/copy.jpg")