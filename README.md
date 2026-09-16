# industrial-quality-inspection.
Developing an automatic computer vision inspection system in Python and OpenCV for manufacturing part inspection for structural boundaries and surface defects. Raw component images are processed in the system using grayscale conversion, Gaussian blurring and Canny edge detection, and the geometry and surface features are automatically extracted from the images using contour extraction algorithms.

Automated build and test pipelines with integrated version control and GitHub Actions CI/CD. The vision architecture has been designed with scalability in mind for use in quality assurance, scale monitoring and automated industrial training and to be interactive as an outreach learning module for STEM automation workshops.

# Core Concept & purpose ⚙️:
Human quality control is slow, expensive, and tiring in high speed manufacturing processes (such as assembly lines, automobile manufacturing, aerospace manufacturing, etc.).

Through Machine Vision this project addresses that problem:

Automated Quality Control: An operator no longer has to inspect each part under a light, but rather an industrial camera takes a picture, and the computer vision algorithm checks the part in mere milliseconds.

Defect & Feature Detection: The script calculates the edge contrast and closed contours and automatically detects cracks, holes missing, surface scratches and other defects that do not meet the required geometric tolerances.

Pass/Fail Decision Logic: The pipeline is used as the "brain" of an automatic conveyor system, with visual output for Pass (green) and Fail (red), and rejection output capability to reject defective components automatically.

With the help of GitHub Actions, every time new defect-detection logic or threshold changes, automated test suites will run to ensure the code is not buggy before being deployed.

# Part Of The CodeSpace 💻
<img width="1550" height="700" alt="Screenshot 2026-09-16 at 2 09 05 pm" src="https://github.com/user-attachments/assets/3ca65525-37d7-4249-97d0-4862a3ebcdd4" />


    import cv2
    import numpy as np
    import os
    
    def inspect_part(image_relative_path):
        # Resolve full path dynamically so it works in any environment
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_image_path = os.path.join(project_root, image_relative_path)
    
        # Check if file exists
        if not os.path.exists(full_image_path):
            print(f"❌ Error: Image file not found at '{full_image_path}'")
            return
    
        # Load component image
        img = cv2.imread(full_image_path)
        if img is None:
            print(f"❌ Error: Unable to decode image at '{full_image_path}'")
            return
    
        # Image Processing Pipeline
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
    
        # Detect contours (structural bounds & defects)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"✅ Inspection Run Success: Detected {len(contours)} features/contours.")
    
        # Annotate detected contours with a green outline
        cv2.drawContours(img, contours, -1, (0, 255, 0), 2)
    
        # Save output image in the same directory as input
        output_path = os.path.join(os.path.dirname(full_image_path), "output_result.png")
        cv2.imwrite(output_path, img)
        print(f"📸 Processed result saved to: '{output_path}'")
    
    if __name__ == "__main__":
        # Point to your test image path
        inspect_part("src/Sample_testing/copy.jpg")

## The First Output:
## Output Explanation: 
Found 8 Contours/Features: OpenCV's findContours function found 8 different boundary paths on the flower (the outline of the petals and inner shading/fold lines).
Look closely at the output_result.png preview pane: you can see thin green outlines around the flower petals. This is the same technique that is employed in a typical industrial vision system for product shape verification, dimension measurement and identifying manufacturing defects, such as scratches or missing parts.
<img width="886" height="532" alt="Screenshot 2026-09-16 at 2 35 58 pm" src="https://github.com/user-attachments/assets/4cfed742-1b03-44b7-b3f5-cb38c236a6d3" />

# Whats Next??
In step 1, add a Quantitative Defect Decision Logic.
To save time and eliminate the need to manually check output_result.png and determine if the gear passes quality control, modify your Python script to calculate quantitative measurements (area, circularity, or number of contours to expect) and produce an auto-generated PASS or FAIL decision.

Step 2: Create a Covered Batch Testing Policy
To avoid having to change the image file path each time, modify inspector.py to process all test images in src/Sample_testing/ in one go, and create a summary report:

Process all .jpg and .png files in the folder and write a script using Python's os.listdir() or glob module.

Inspection Report: Generate a console output with a structured summary of the inspection result of each of the tested components (e.g. gear.jpg: PASS, broken_gear.jpg: REJECT).
