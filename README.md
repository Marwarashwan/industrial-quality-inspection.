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

# Industry Implementations for Quality Inspection & Edge Automation
## Automated Quality Assurance & Defect Detection (Manufacturing)
1. On the production lines, computer vision edge inspection pipelines can be used to automate visual quality control, such as the Canny edge detection and contour extraction scripts you created.

2. Component Verification & Geometry Checks: Check mechanical components such as gears, stamped metal, molded plastic etc. against reference parts. The system notifies in real time if any gear teeth are missing, if the gears have warped, or if the dimension is incorrect.

3. Surface Flaw Detection: Detecting scratches, cracks, misaligned labels or even missing parts on a high-speed conveyor belt without human intervention.

4. Sorting & Grading Systems: Automatic sorting of physical products into Quality Grades (PASS/FAIL/REJECT) from visual surface properties or perimeters of the contour.


## Smart Industrial Automation & IIoT (Industry 4.0)
1. Edge hardware solutions such as Raspberry Pi and microcontrollers can be paired with a light-weight web framework and cloud connectivity to provide a remote way to monitor the factories.

2. Remote Equipment Monitoring: Embedded web dashboards (such as Flask web servers) can be installed on edge equipment to enable plant managers to check the status of equipment, switch system relays, and visualize real-time sensor metrics remotely.

3. Predictive Maintenance & Telemetry: Sensor data delivered to cloud platforms (such as AWS IoT Core or ThingSpeak) via MQTT or HTTPS, and send alerts to maintenance staff before the hardware fails.

4. Automated Surveillance & Safety: Edge-based security cameras with motion detection record unauthorized access activity, alert visually over local networks in real-time and protect restricted areas in the factory.

## Interactive Simulation & Human-Machine Interfaces (HMI)
1. When physical microcontrollers are directly connected to 3D game engines or user interfaces, hardware in the loop (HIL) testing environments and training tools are created.

2. Digital Twin Visualization: Data transmitted via serial connections allows physical machines to be connected to virtual 3D models in Unity or Unreal Engine, displaying actual hardware behavior in real time, and thus forming a "Digital Twin.

3. Operator Training Simulators: These enable technicians to practice on complex industrial control layouts in a safe environment, using tactile control boards, button panels and physical feedback systems in conjunction with virtual environments.

4. Interactive Quality Stations: Physical HMI console stations with audio-visual indicators (buzzers, LEDs and displays) which direct the assembly operator through the manual routines of product assembly step-by-step.

## The Code for The Sample Pictures:
<img width="1092" height="769" alt="Screenshot 2026-09-17 at 9 37 19 am" src="https://github.com/user-attachments/assets/55d86039-2465-4efc-85f5-465e08c9cce1" />

# STEP TWO: TESTING ACTUAL GEAR PICTURES AND ANALYSE IT 📑:
<img width="915" height="586" alt="Screenshot 2026-09-17 at 10 50 37 am" src="https://github.com/user-attachments/assets/12fbb260-53ab-49ad-a435-843cd0c2a929" />

Git Sync & Push Success
Your rebase included remote changes without any conflict and you have your commit with batch_inspector.py and test assets up and running in GitHub.

The Contour Extraction & Decision Engine Execution is an executable application that processes the extracted contours to make decisions.
The script ran the image, found 8 raw contours, removed the smallest ones (< 100 pixels), and matched 4 major contours to your classification rule for the Spur / External Gear (Solidity < 0.75).

What are the reasons that there is no output image yet?

Your batch_inspector.py script now reads and computes the contour geometry, but it's lacking the contour-drawing and file-writing OpenCV functions (cv2.drawContours, cv2.putText, or cv2.imwrite).

To save an annotated output_result.png image with green overlays and text labels, add rendering steps right before saving the image file.

Key Upgrades & Fixes Applied

Safe File Loading Strategy: Implicit test for img is None, added explicit test for this. This prevents cv2.cvtColor from throwing a fatal (-215:Assertion failed) !_src.empty() assertion crash if an image path is invalid or missing.

Sensitivity & Noise Thresholding: reduced the noise filtering area from < 500 to < 100. This will enable smaller mechanical contours or finer tooth profiles to register rather than being ignored silently.

The integrated cv2 is the Feature Extraction & Classification Pipeline.Directly included convexHull and perimeter metrics in the classification decision tree (Solidity and Circularity calculation) for automatic differentiation of the gear geometry.

Console Telemetry: Added logging (Total raw contours found, individual Contour Area printouts, and -> MATCH statements) for real-time feedback on the vision pipeline's performance on the console.

# THE CODE:
    import cv2
    import numpy as np
    
    def classify_gear(image_path, output_path="src/Sample_testing/output_result.png"):
        img = cv2.imread(image_path)
        if img is None:
            print(f"Could not open image at {image_path}")
            return
    
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
    
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"Total raw contours found: {len(contours)}")
    
        # Create a copy of the image to draw visual overlays on
        annotated_img = img.copy()
    
        for cnt in contours:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
    
            print(f"Contour Area: {area:.1f} | Perimeter: {perimeter:.1f}")
    
            if perimeter == 0 or area < 100: 
                continue 
    
            # Calculate shape descriptors
            circularity = (4 * np.pi * area) / (perimeter ** 2)
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0
    
            # Classification decision rules
            if solidity < 0.75:
                gear_type = "Spur / External Gear"
                color = (0, 255, 0)  # Green for detected gear contours
            elif circularity > 0.85:
                gear_type = "Smooth Bearing"
                color = (255, 0, 0)  # Blue for circular profiles
            else:
                gear_type = "Internal / Special Gear"
                color = (0, 165, 255) # Orange for internal features
    
            print(f"-> MATCH: {gear_type} | Solidity: {solidity:.2f} | Circularity: {circularity:.2f}")
    
            # Draw contour outline on the output image
            cv2.drawContours(annotated_img, [cnt], -1, color, 2)
    
        # Save the visual inspection output image
        cv2.imwrite(output_path, annotated_img)
        print(f"\nVisual inspection output saved to: {output_path}")
    
    classify_gear("src/Sample_testing/copy.jpg")
