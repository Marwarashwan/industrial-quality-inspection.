# Industrial Quality Inspection.
Developing an automatic computer vision inspection system in Python and OpenCV for manufacturing part inspection for structural boundaries and surface defects. Raw component images are processed in the system using grayscale conversion, Gaussian blurring and Canny edge detection, and the geometry and surface features are automatically extracted from the images using contour extraction algorithms.

Automated build and test pipelines with integrated version control and GitHub Actions CI/CD. The vision architecture has been designed with scalability in mind for use in quality assurance, scale monitoring and automated industrial training.

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

## STEP-1: TESTING THE CODE + THE ML MODEL AND DEBUGGING PROCESS 📑 ✅:
<img width="1092" height="769" alt="Screenshot 2026-09-17 at 9 37 19 am" src="https://github.com/user-attachments/assets/55d86039-2465-4efc-85f5-465e08c9cce1" />
## ACTUAL GEAR ANALYSIS:
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
    import os
    import glob
    
    def classify_gear(image_path, output_dir="src/Sample_testing"):
        img = cv2.imread(image_path)
        if img is None:
            print(f"Could not open image at {image_path}")
            return
    
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
    
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        annotated_img = img.copy()
    
        for cnt in contours:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
    
            if perimeter == 0 or area < 1000 or area > (img.shape[0] * img.shape[1] * 0.9): 
                continue 
    
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / h
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0
    
            # Gear classification logic
            if 0.8 <= aspect_ratio <= 1.2 and 0.40 <= solidity <= 0.85:
                gear_type = "Spur / External Gear"
                color = (0, 255, 0)
            else:
                gear_type = "Non-Gear / Irregular Object"
                color = (0, 0, 255)
    
            print(f"[{os.path.basename(image_path)}] {gear_type} | Solidity: {solidity:.2f} | Aspect Ratio: {aspect_ratio:.2f}")
    
            cv2.drawContours(annotated_img, [cnt], -1, color, 2)
            cv2.putText(annotated_img, gear_type, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
        # Save output using the original filename
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(image_path)
        output_path = os.path.join(output_dir, f"result_{filename}")
        cv2.imwrite(output_path, annotated_img)
    
    if __name__ == "__main__":
        # Automatically scan and process all images in src/images/
        image_files = glob.glob("src/images/*.[jJ][pP]*[gG]") + glob.glob("src/images/*.webp")
        print(f"Found {len(image_files)} images to process in src/images/\n")
        for img_path in image_files:
            classify_gear(img_path)


# Final Results:
<img width="1329" height="819" alt="Screenshot 2026-09-17 at 12 11 16 pm" src="https://github.com/user-attachments/assets/0384acd9-18d0-4f4e-b6f1-a27a8233ea56" />
<img width="1329" height="819" alt="Screenshot 2026-09-17 at 12 10 56 pm" src="https://github.com/user-attachments/assets/e3f438e0-23d6-4a16-b024-b18d4034371e" />
<img width="1329" height="819" alt="Screenshot 2026-09-17 at 12 10 42 pm" src="https://github.com/user-attachments/assets/daf33678-fbc8-4aff-b58a-cbff1345c04d" />

## 1. The shift to Machine Learning (ML) is underway.The shift to Machine Learning (ML) is in progress.

The traditional OpenCV geometry rules (solidity, circularity, aspect ratio) are effective with clean images but not with real industrial scenes such as light variations, rust, shadows, surface wear, etc. Machine Learning enables your system to adjust to these real world conditions:

Old-fashioned OpenCV (What you're used to): You write hardcoded geometric rules by hand (e.g., if solidity < 0.75). If a gear has any minor nick, missing tooth or greasy smudge, the solidity calculation is reduced and you break your rule.

Classical ML (SVM / Random Forest): You provide extracted OpenCV measurements (area, perimeter, solidity, circularity, number of convex hull defects) to an ML classifier, rather than manually writing if / else rules. The algorithm is trained to distinguish between "Good Gear," "Defective Gear," and "Non-Gear" based on its optical characteristics.

Instead of manually measuring contours, the Deep Learning (YOLOv8 / CNNs) approach examines raw pixels directly. It automatically detects, crops, and classifies complex multi-gear gearboxes, worn teeth and surface defects even in the dark or heavy rust.

The recommended Next Step is to remain using OpenCV feature extraction for the time being, but store the metrics that you calculated (solidity, circularity, aspect_ratio) in a CSV file. Next, it will be the exact training data required to train a Scikit-Learn ML model!

## 2. Simplifying Visual Outputs

When the contrast of gear images is high, the background is textured or rusty, cv2.findContours identifies hundreds of small pieces of edges. If you draw all the fragments, then you're left with messy, confusing lines.

Use these refined targeted enhancements in src/batch_inspector.py to create clean, professional overlays:

Use a high contour area filter for small noise (e.g., area < 2500) to eliminate very small surface features and background flecks.

To draw the External Gear Profile: Pass cv2.Replace cv2. with RETR_EXTERNAL.While drawing main overlays use RETR_TREE to draw only the outermost silhouette and not each and every little internal shadow line.

Smooth Out the Contour Overlays: Use cv2.approxPolyDP: Approximate and smooth jagged edges of pixel boundaries before calling cv2.drawContours.

Clean Text & Bounding Boxes: Draw a clean rectangle around the main gear detected, and label it on a separate dark background card above its top.

# The Clean Version (Before testing):
    import cv2
    import numpy as np
    import os
    import glob
    
    def classify_gear(image_path, output_dir="src/Sample_testing"):
        img = cv2.imread(image_path)
        if img is None:
            print(f"Could not open image at {image_path}")
            return

    # 1. Preprocessing: Grayscale & Stronger Blur to smooth out noise/rust
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    edges = cv2.Canny(blurred, 30, 120)

    # 2. Extract ONLY external outer profiles to prevent internal messy lines
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    annotated_img = img.copy()

    img_area = img.shape[0] * img.shape[1]

    for cnt in contours:
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, True)

        # AGGRESSIVE FILTERING: Ignore background noise (< 2500px) and full-image frames (> 85%)
        if perimeter == 0 or area < 2500 or area > (img_area * 0.85): 
            continue 

        # Smooth out contour edges using Ramer-Douglas-Peucker algorithm
        epsilon = 0.005 * perimeter
        smoothed_cnt = cv2.approxPolyDP(cnt, epsilon, True)

        # Feature Metrics
        x, y, w, h = cv2.boundingRect(smoothed_cnt)
        aspect_ratio = float(w) / h
        hull = cv2.convexHull(smoothed_cnt)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0

        # Classification Rules
        if 0.75 <= aspect_ratio <= 1.25 and 0.35 <= solidity <= 0.88:
            gear_type = "Spur / External Gear"
            color = (0, 255, 0) # Clean Green
        else:
            gear_type = "Non-Gear / Irregular"
            color = (0, 0, 255) # Red

        print(f"[{os.path.basename(image_path)}] {gear_type} | Solidity: {solidity:.2f} | Aspect Ratio: {aspect_ratio:.2f}")

        # Draw smooth, thick outline
        cv2.drawContours(annotated_img, [smoothed_cnt], -1, color, 3)

        # Render a clean text banner background for readability
        label = f"{gear_type} ({solidity:.2f})"
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(annotated_img, (x, y - text_h - 12), (x + text_w + 10, y), (0, 0, 0), -1)
        cv2.putText(annotated_img, label, (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Save output
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(image_path)
    output_path = os.path.join(output_dir, f"result_{filename}")
    cv2.imwrite(output_path, annotated_img)

    if __name__ == "__main__":
        image_files = glob.glob("src/images/*.[jJ][pP]*[gG]") + glob.glob("src/images/*.webp")
        print(f"Processing {len(image_files)} gear images with clean overlay rendering...\n")
        for img_path in image_files:
            classify_gear(img_path)


## Inspection Summary CSV

<img width="1254" height="452" alt="Screenshot 2026-09-21 at 11 47 50 am" src="https://github.com/user-attachments/assets/90c8fd69-2637-4428-9362-aeceecd7965d" />

filename,object_id,area,perimeter,solidity,circularity,aspect_ratio,classification
images-2.jpg,1,2964.5,203.58,0.9883,0.8989,1.0,Non-Gear / Irregular
images copy.jpg,1,8167.0,378.19,0.9803,0.7175,0.9826,Non-Gear / Irregular
images copy.jpg,2,8348.0,599.75,0.8177,0.2916,1.0328,Spur / External Gear
images copy.jpg,3,8285.5,378.23,0.9808,0.7278,0.8943,Non-Gear / Irregular
images copy.jpg,4,8774.5,388.78,0.9851,0.7295,0.9091,Non-Gear / Irregular
large-industrial-old-heavy-rusted-260nw-2706226599.webp,1,2740.0,992.57,0.5304,0.0349,1.25,Non-Gear / Irregular
large-industrial-old-heavy-rusted-260nw-2706226599.webp,2,2564.5,988.19,0.3928,0.033,1.7286,Non-Gear / Irregular
large-industrial-old-heavy-rusted-260nw-2706226599.webp,3,2702.0,1314.56,0.3679,0.0196,0.617,Non-Gear / Irregular
large-industrial-old-heavy-rusted-260nw-2706226599.webp,4,2714.5,298.01,0.9301,0.3841,0.9437,Spur / External Gear
large-industrial-old-heavy-rusted-260nw-2706226599.webp,5,2745.0,788.47,0.4545,0.0555,1.6962,Non-Gear / Irregular

<img width="889" height="616" alt="Screenshot 2026-09-21 at 11 42 54 am" src="https://github.com/user-attachments/assets/067742f7-e30b-4afe-9354-c1e3d505334c" />

## The Code 👩🏻‍💻:
    import cv2
    import numpy as np
    import os
    import glob
    import csv
    
    def process_and_log_gears(image_dir="src/images", output_dir="src/Sample_testing"):
        os.makedirs(output_dir, exist_ok=True)
        csv_path = os.path.join(output_dir, "inspection_summary.csv")
        
        image_files = glob.glob(f"{image_dir}/*.[jJ][pP]*[gG]") + glob.glob(f"{image_dir}/*.webp") + glob.glob(f"{image_dir}/*.png")
        
        csv_headers = ["filename", "object_id", "area", "perimeter", "solidity", "circularity", "aspect_ratio", "classification"]
        
        with open(csv_path, mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(csv_headers)
    
            for img_path in image_files:
                filename = os.path.basename(img_path)
                img = cv2.imread(img_path)
                if img is None:
                    continue
    
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                edges = cv2.Canny(blurred, 50, 150)
    
                # Use RETR_EXTERNAL to grab outer silhouettes instead of inner spokes
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                annotated_img = img.copy()
                img_area = img.shape[0] * img.shape[1]
                object_count = 0
    
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    perimeter = cv2.arcLength(cnt, True)
    
                    # Filter out background boundaries and small noise
                    if perimeter == 0 or area < 1500 or area > (img_area * 0.85):
                        continue
    
                    object_count += 1
    
                    # Calculate metrics directly on raw contours for accurate tooth cutouts
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(w) / h
                    circularity = (4 * np.pi * area) / (perimeter ** 2)
                    
                    hull = cv2.convexHull(cnt)
                    hull_area = cv2.contourArea(hull)
                    solidity = float(area) / hull_area if hull_area > 0 else 0
    
                    # Adjusted classification rule: Gears with teeth typically have solidity 0.65 - 0.98
                    if 0.75 <= aspect_ratio <= 1.25 and 0.60 <= solidity <= 0.98:
                        classification = "Spur / External Gear"
                        color = (0, 255, 0) # Green
                    else:
                        classification = "Non-Gear / Irregular"
                        color = (0, 0, 255) # Red
    
                    writer.writerow([filename, object_count, round(area, 2), round(perimeter, 2), round(solidity, 4), round(circularity, 4), round(aspect_ratio, 4), classification])
    
                    cv2.drawContours(annotated_img, [cnt], -1, color, 3)
                    label = f"{classification} (#{object_count})"
                    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    cv2.rectangle(annotated_img, (x, y - text_h - 10), (x + text_w + 10, y), (0, 0, 0), -1)
                    cv2.putText(annotated_img, label, (x + 5, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
                output_path = os.path.join(output_dir, f"result_{filename}")
                cv2.imwrite(output_path, annotated_img)
                print(f"Processed: {filename} -> Found {object_count} object(s)")
    
    if __name__ == "__main__":
        process_and_log_gears()



## Important Notes 📝:
Phase 1: Basic Edge Detection & Features (Done) — Were able to correctly install OpenCV, detect shape contours, compute basic metrics (Solidity, Circularity, Aspect Ratio) and apply overlays.

Phase 2: Edge Case Debugging & CSV Data Logging (Where you are now), it learned that inner cutouts (spokes) work with cv2.The code also failed to convert the image of the flagging sub-components into cv2.approxPolyDP rounded off the edges of the fine teeth of the gears. This feedback loop is crucial since it will identify where static if/else rules break.

Phase 3: Robust Preprocessing & Outer Profile Isolation (Next Step), the focus shifts to cv2 and robust pre-processing, as well as outer profile isolation.All gear boundaries are isolated using this combination of RETR_EXTERNAL, fine-tuning Canny thresholds, and eliminating over-smoothing.

Phase 4: Machine Learning Classification — After the pipeline starts logging accurate and uncorrupted feature measurements in inspection_summary.csv, we can replace the fragile and error-prone manually-written threshold rules with an ML model trained directly on inspection_summary.csv.

This project is built on a solid architectural foundation as it is based on batch processing, automated visual output of debugging, structured feature extraction and CSV logging. Once its executed the updated script that extracts outer boundaries, your metrics, classifications will match.
