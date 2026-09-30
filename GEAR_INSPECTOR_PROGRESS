# Gear Inspection Project — Progress Log

**Project:** `industrial-quality-inspection`
**Goal:** Automatically detect gears in photos, classify them (gear vs. non-gear), and measure tooth count / radii accurately enough to feed a MATLAB gear-train simulation.

---

## 1. Where we started

The original script (`inspector.py` / early `batch_inspector.py`) used:
- Grayscale + Otsu thresholding to separate objects from background
- Contour area, perimeter, solidity, circularity, aspect ratio as features
- A rule-based fallback, or a Random Forest trained on the script's **own previous output**

### Problems found in the original version

| # | Problem | Why it mattered |
|---|---|---|
| 1 | **Otsu thresholding** assumes background is much brighter/darker than the object. On a mid-tone rusty gear, it failed and picked up the gear's open **spoke windows** as separate "objects." | The tool was detecting empty triangular gaps in a wheel and mislabeling them as "Non-Gear" or even "Spur/Gear" — the actual gear body was never analyzed correctly. |
| 2 | **The learning loop was circular.** The Random Forest trained on `inspection_summary.csv`, but that CSV's labels came from the rule-based logic (or the model itself on later runs). Without manual correction, the model just learned to copy its own guesses. | Confidence scores looked good, but the model wasn't learning anything new — it was memorizing its own mistakes. |
| 3 | **The CSV was overwritten every run.** | "Historical logs" were never more than the last run's output — no real accumulation of verified training data. |
| 4 | Features like raw `area` and `perimeter` **change with photo zoom/distance**, so the same gear photographed differently produced different numbers. | Inconsistent results across otherwise-identical gears. |

---

## 2. Rebuild — first pass

**Fix:** Rewrote the segmentation to estimate the background color from a thin border around the image, then keep any pixel that differs from it (works for dark, rusty, light, or colored gears — not just bright-background photos). Contours were filled solid so spoke windows became part of the gear body instead of separate false objects.

**Fix — tooth counting via FFT:** Instead of crude shape stats, the outline is unrolled into "distance from center vs. angle," and an FFT finds the strongest repeating pattern — that repeat count *is* the tooth count. This also gives clean, scale-invariant features (circularity, solidity, tooth depth, etc.) that don't drift with zoom level.

**Fix — real training data:** Instead of learning from its own guesses, the Random Forest now trains on **6,000 synthetically generated shapes** — gears with 8 to 120 teeth in varied proportions, plus circles, hex nuts, stars, blobs, and (critically) rounded spoke-window shapes, so it explicitly learns to reject the exact false positive that broke the original script.

**Fix — meshing gears:** Added a distance-transform-based split so two touching/meshing gears in one photo are correctly separated into two objects instead of read as one blob.

**Fix — correction loop:** Added `review_me.csv` + `--learn`, so verified real corrections (not the model's own guesses) get folded back into training, weighted 10x a synthetic example.

**Fix — one file:** Multiple back-and-forth attempts to get a 4-file version (`gear_core.py`, `synth.py`, `train_model.py`, `batch_inspector.py`) onto the Codespace via copy-paste kept failing — files landed with the wrong name, in the wrong folder, or not at all, causing repeated `ModuleNotFoundError`. Consolidated everything into a single file, `gear_inspector.py`, so there was nothing left to go missing.

---

## 3. Bugs found during testing (this session)

### 3.1 Tight crops read as "cropped at border"

**Symptom:** Two of your three test photos came back "0 gears" — flagged `cropped at border` even though the whole gear was visible in the photo, just touching the image's raw edge (common for stock photos with zero margin).

**Fix:** The script now adds a plain white border (~12% of image size) around every photo *before* looking for objects. A gear that only looked cropped because the photo itself had no margin now gets measured properly. A gear that's genuinely cut off by the camera (missing teeth) still can't be recovered — that's real missing data, not a bug.

**Verified:** Your real photo `images-2.jpg` went from "0 gears / cropped" to correctly reading **51 teeth**.

### 3.2 Meshing-gear split was too strict (found while testing the fix above)

**Symptom:** A tightly meshing pair of gears (small gear touching a big one, like a stock "gear set" photo) was being read as one merged blob instead of two gears, because the geometric test for "is there a real gap between these two round shapes" required a deeper valley than a tight mesh actually has.

**Fix:** Loosened the acceptance threshold (`NECK_FACTOR`) after testing multiple values against both a synthetic tight mesh (needs it loose) and a synthetic 3-gear chain + solo gears (need it strict enough not to invent phantom extra objects). Landed on a value that passes all of them, and exposed it as a `--neck-factor` command-line option so you can tune it yourself per-photo without needing new code each time.

**Also tried and rejected:** A more "textbook" watershed-based split (standard technique for touching circular objects). It handled 2-gear cases fine but broke a 3-gear chain, over-assigning pixels to one gear and starving the others. Reverted to the simpler, verified-working method rather than ship something with a known regression.

### 3.3 `.gif` files silently ignored

**Symptom:** One of your real gear photos was a `.gif` (a worm-gear diagram) and was silently skipped — the script's list of recognized file extensions didn't include `.gif`, so it never even appeared in the "Inspecting N images" count.

**Fix:** Added `gif` to the recognized extensions list.

---

## 4. Real-photo test results (6 of your actual images)

| # | Photo | Result | Why |
|---|---|---|---|
| 1 | Black plastic spur gear (flat, face-on) | ✅ Correct — 51 teeth | Exactly the kind of photo this method is built for |
| 2 | Rusty spoked wheel (flat, face-on) | ✅ Correct — 73 teeth | Same as above |
| 3 | Worm gear + spur gear | ❌ Fails | The worm gear is a screw-thread on a cylinder, not a flat disk with teeth — a fundamentally different shape this outline-based method can't read. The `.gif` bug also hid this one until fixed. |
| 4 | Herringbone gear | ❌ Fails | Photographed at an angle (3D render), not face-on — the outline isn't a simple circle-with-teeth from this viewpoint |
| 5 | Two meshing gears (illustration) | ❌ Fails | Subtly drawn at a slight perspective angle (a true circle looks like a faint oval) — same root cause as #4 |
| 6 | Spiral bevel gear set | ❌ Fails | Same as #4 — angled 3D render |

### The pattern

**This tool is accurate specifically for flat, face-on photographs of real gears** (#1 and #2 — both succeeded). It is *not* built to handle:
- Gears photographed or rendered at an angle (perspective distorts the circular outline)
- Non-disk gear types (worm gears, and by extension screws/helical shafts)

These aren't bugs to keep patching — they need a fundamentally different computer-vision approach (perspective correction / 3D pose estimation, or thread-pattern detection for worm gears), which is a separate project scope, not a fix to this one.

---

## 5. What's still open / to verify

- [ ] Confirm accuracy holds up across your full training photo set (30–50 photos), not just these 6
- [ ] Use `review_me.csv` + `--learn` to correct any remaining wrong labels on **flat, face-on photos only**
- [ ] Set aside ~10 photos you never correct, as an honest held-out accuracy check
- [ ] Locate (or re-photograph) the earlier `images copy.jpg` meshing-pair test case, if you still want it specifically diagnosed — not among the 6 photos tested above

---

## 6. Next step: MATLAB implementation

**Do this only after accuracy on your flat, face-on training photos looks solid.** Feeding MATLAB numbers from an already-known-bad detection just moves the same problem one step later.

### What the pipeline already outputs for MATLAB

Every run produces `gear_params.json`, containing for each image:
- `tooth_count`, `pitch_radius_px`, `tip_radius_px`, `root_radius_px` per detected gear
- `cx`, `cy` — each gear's center point
- `meshing_pairs` — for any two gears that touch, their computed gear ratio (cross-checked two ways: from tooth counts, and from pitch radii, flagged `consistent: true/false`)

This is already close to what a gear-train simulation needs: tooth counts and radii to build each gear, ratios to define how they turn together, centers to place them relative to each other.

### The one gap: real-world scale

Everything above is measured in **pixels**, because that's all a photo can give you. MATLAB needs real units (mm, inches). To bridge this:

1. **Pick one known reference measurement per photo** — e.g., "this gear's outer diameter is 80mm" (measured with calipers, or from a datasheet if it's a catalog part).
2. Compute a `pixels_per_mm` scale factor from that one measurement.
3. Multiply every other pixel measurement in `gear_params.json` by `1 / pixels_per_mm` to get millimeters.

### Suggested MATLAB build order

1. **Import `gear_params.json`** (MATLAB's `jsondecode` reads it directly).
2. **Build one gear object per entry** — tooth count, pitch radius (converted to mm), position.
3. **For each `meshing_pairs` entry**, define the kinematic constraint between the two gears (angular velocity ratio = inverse of the tooth-count ratio).
4. **Animate/simulate** rotation propagating through the gear train, using the ratios already computed.
5. **Validate**: pick a known real gear train (even a simple 2-gear reduction) and confirm MATLAB's simulated ratio matches the physical part's actual ratio, before trusting it on gears you've only measured from photos.

---

## Files delivered this session

- `gear_inspector.py` — the current, single-file version of the pipeline (segmentation, feature extraction, synthetic training data, Random Forest, batch runner, all in one file)

## Key commands

```bash
# Run inspection (auto-trains model on first run)
python3 src/gear_inspector.py

# Force retrain from scratch
python3 src/gear_inspector.py --retrain

# Adjust how easily two touching gears get split apart
python3 src/gear_inspector.py --neck-factor 0.8   # raise if 2 real gears keep merging into 1
python3 src/gear_inspector.py --neck-factor 0.4   # lower if 1 gear keeps getting split into fake extras

# Fold your corrections from review_me.csv into training
python3 src/gear_inspector.py --learn src/Sample_testing/review_me.csv
```
