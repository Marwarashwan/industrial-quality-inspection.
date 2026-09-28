"""
gear_inspector.py - ONE FILE: detect, classify and measure gears in a folder of images.

Everything lives here on purpose (segmentation, feature extraction, synthetic-data
generator, Random Forest trainer, and the batch runner) so there is nothing else to
import and nothing else that can go missing.

USAGE
-----
    python3 gear_inspector.py
        -> reads every image in src/images, writes annotated images + CSVs +
           gear_params.json into src/Sample_testing. Trains the model on first run
           (30-60s), reuses it after that (instant).

    python3 gear_inspector.py --images src/images --out src/Sample_testing

    python3 gear_inspector.py --retrain
        -> forces the model to retrain from scratch.

    python3 gear_inspector.py --learn src/Sample_testing/review_me.csv
        -> after you correct the 'true_label' column in review_me.csv (values:
           "Gear" or "Non-Gear"), run this to fold your corrections into training,
           then retrains. Your corrections count 10x a synthetic example.

OUTPUTS (in --out folder)
--------------------------
    result_<image>          annotated copy: green=gear, red=non-gear, yellow=unsure,
                             orange=cropped at image border (not classified)
    inspection_summary.csv  every detected object + its measurements + prediction
    review_me.csv           same rows, with a blank 'true_label' column for you to
                             fill in and feed back with --learn
    gear_params.json        per image: gear centres/radii/tooth counts + meshing
                             pairs + gear ratios -> this is the file to hand to MATLAB
"""
import argparse
import csv
import glob
import json
import os
import sys

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Paths (all relative to THIS file, so it works no matter what folder you run
# python3 from)
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "models", "gear_rf.joblib")
REAL_PATH = os.path.join(HERE, "training_data", "real_labeled.csv")
REAL_WEIGHT = 10.0          # one of your verified examples counts as 10 synthetic ones
UNSURE_BELOW = 0.70          # confidence under this -> flagged yellow, needs a human look
IMG_EXTS = ("jpg", "jpeg", "png", "webp", "bmp", "tif", "tiff")

GEAR = "Spur / External Gear"
NON_GEAR = "Non-Gear / Irregular"

# All 12 features are scale- and rotation-invariant: a gear photographed close up or
# far away, or turned upside down, produces (almost) the same numbers.
FEATURE_NAMES = [
    "circularity",     # 4*pi*Area / Perimeter^2  (1.0 = perfect circle)
    "solidity",        # Area / convex-hull area   (low if teeth stick out a lot)
    "aspect_ratio",    # short side / long side of the rotated bounding box
    "extent",          # Area / rotated-box area
    "fill_circle",     # Area / area of the smallest enclosing circle
    "elongation",      # 2nd Fourier harmonic of the outline (oval-ness)
    "radial_std",      # std(radius) / mean(radius) around the outline
    "tooth_depth",     # 1 - (5th percentile radius / 95th percentile radius)
    "dominant_k",      # strongest repeating pattern around the outline = tooth count
    "tooth_strength",  # amplitude of that pattern, relative to the mean radius
    "tooth_purity",    # how much of all the outline "wiggle" is that one pattern
    "harmonic_2",      # 2nd harmonic of the tooth pattern / 1st (tooth shape)
]
N_BINS = 720


# ===========================================================================
# 1. SEGMENTATION - find the gear silhouette(s) in an image
# ===========================================================================
def segment_foreground(img_bgr):
    """Binary mask (uint8 0/255) of everything that isn't background.

    Estimates the background colour from a thin border around the image, then keeps
    any pixel whose colour differs enough from it. This adapts to dark, rusty, light
    or coloured gears, unlike a single global brightness threshold. Contours are
    filled solid so open spoke windows become part of the gear body (this is exactly
    what the earlier version of this script got wrong - it detected the windows as
    separate "gear" objects).
    """
    h, w = img_bgr.shape[:2]
    blur = cv2.GaussianBlur(img_bgr, (5, 5), 0)
    lab = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB).astype(np.float32)

    b = max(4, int(0.03 * min(h, w)))
    border = np.concatenate([
        lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
        lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    border_dist = np.linalg.norm(border - bg, axis=1)
    noise = np.percentile(border_dist, 90)
    thr = float(np.clip(3.0 * noise + 8.0, 14.0, 50.0))

    dist = np.linalg.norm(lab - bg, axis=2)
    mask = (dist > thr).astype(np.uint8) * 255

    k = max(3, int(0.006 * min(h, w)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    solid = np.zeros_like(mask)
    cv2.drawContours(solid, contours, -1, 255, thickness=cv2.FILLED)
    return solid


def split_touching(solid):
    """Split a blob containing several meshing/overlapping gears into separate masks.

    Uses a distance transform: each round gear has one peak at its centre, the
    height of the peak is roughly its radius. Peaks are accepted largest-first if
    they're outside an already-accepted gear's circle AND separated from it by a
    narrow neck (real contact between two gears, not one big blob).
    """
    dt = cv2.distanceTransform(solid, cv2.DIST_L2, 5)
    dmax = float(dt.max())
    if dmax < 6:
        return [solid]

    local_max = cv2.dilate(dt, np.ones((9, 9), np.uint8))
    ys, xs = np.where((dt >= local_max - 1e-6) & (dt > 0.12 * dmax))
    order = np.argsort(-dt[ys, xs])[:3000]

    seeds = []
    for i in order:
        x, y, r = int(xs[i]), int(ys[i]), float(dt[ys[i], xs[i]])
        if not seeds:
            seeds.append((x, y, r))
            continue
        if any(np.hypot(x - sx, y - sy) < 0.9 * sr for sx, sy, sr in seeds):
            continue
        sx, sy, sr = min(seeds, key=lambda s: np.hypot(x - s[0], y - s[1]))
        t = np.linspace(0, 1, 60)
        lx = np.clip((sx + (x - sx) * t).astype(int), 0, dt.shape[1] - 1)
        ly = np.clip((sy + (y - sy) * t).astype(int), 0, dt.shape[0] - 1)
        if dt[ly, lx].min() < 0.5 * min(r, sr):     # a real neck between the two
            seeds.append((x, y, r))

    if len(seeds) == 1:
        return [solid]

    yy, xx = np.nonzero(solid)
    score = np.stack([np.hypot(xx - sx, yy - sy) - sr for sx, sy, sr in seeds], axis=1)
    owner = np.argmin(score, axis=1)
    parts = []
    for i in range(len(seeds)):
        m = np.zeros_like(solid)
        m[yy[owner == i], xx[owner == i]] = 255
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        parts.append(m)
    return parts


# ===========================================================================
# 2. FEATURES - turn a contour into the 12 numbers the classifier uses
# ===========================================================================
def radial_profile(cnt, n=N_BINS):
    """Distance from centroid to outline, sampled at n equally spaced angles."""
    m = cv2.moments(cnt)
    if m["m00"] == 0:
        return None, None
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    pts = cnt.reshape(-1, 2).astype(np.float64)
    dx, dy = pts[:, 0] - cx, pts[:, 1] - cy
    ang = np.arctan2(dy, dx)
    r = np.hypot(dx, dy)
    idx = ((ang + np.pi) / (2 * np.pi) * n).astype(int) % n
    sums = np.bincount(idx, weights=r, minlength=n)
    cnts = np.bincount(idx, minlength=n)
    ok = cnts > 0
    if ok.sum() < 16:
        return None, None
    x = np.arange(n)
    prof = np.interp(x, x[ok], sums[ok] / cnts[ok], period=n)
    return prof, (cx, cy)


def extract_features(cnt):
    """Return (features_dict, geometry_dict) for one contour, or (None, None).

    The tooth-related features (dominant_k, tooth_strength, tooth_purity) come from
    an FFT of the radial profile: a gear's outline repeats once per tooth as you go
    around it, so the strongest frequency in that signal IS the tooth count.
    """
    area = cv2.contourArea(cnt)
    per = cv2.arcLength(cnt, True)
    if area < 100 or per == 0:
        return None, None
    prof, centre = radial_profile(cnt)
    if prof is None:
        return None, None

    mean_r = float(prof.mean())
    spec = np.abs(np.fft.rfft(prof - mean_r)) * 2.0 / len(prof) / mean_r
    kmax = max(6, min(N_BINS // 4, len(cnt) // 4))
    band = spec[3:kmax + 1]
    k = int(np.argmax(band)) + 3
    strength = float(spec[k])
    purity = float(spec[k] ** 2 / (np.sum(band ** 2) + 1e-12))
    harm2 = float(spec[2 * k] / (spec[k] + 1e-12)) if 2 * k < len(spec) else 0.0

    hull_area = cv2.contourArea(cv2.convexHull(cnt))
    (_, _), (rw, rh), _ = cv2.minAreaRect(cnt)
    (_, _), enc_r = cv2.minEnclosingCircle(cnt)
    p5, p95 = np.percentile(prof, [5, 95])

    feats = {
        "circularity": 4 * np.pi * area / per ** 2,
        "solidity": area / hull_area if hull_area > 0 else 0.0,
        "aspect_ratio": min(rw, rh) / max(rw, rh) if max(rw, rh) > 0 else 0.0,
        "extent": area / (rw * rh) if rw * rh > 0 else 0.0,
        "fill_circle": area / (np.pi * enc_r ** 2) if enc_r > 0 else 0.0,
        "elongation": float(spec[2]),
        "radial_std": float(prof.std() / mean_r),
        "tooth_depth": float(1.0 - p5 / p95) if p95 > 0 else 0.0,
        "dominant_k": k,
        "tooth_strength": strength,
        "tooth_purity": purity,
        "harmonic_2": harm2,
    }
    tip_r, root_r = np.percentile(prof, [97, 3])
    geom = {
        "cx": centre[0], "cy": centre[1],
        "tip_radius_px": float(tip_r), "root_radius_px": float(root_r),
        "pitch_radius_px": float((tip_r + root_r) / 2),
        "tooth_count": k, "area_px": float(area),
    }
    return {n: float(feats[n]) for n in FEATURE_NAMES}, geom


def rule_based_label(f):
    """Physics-style fallback, used only if no trained model can be loaded at all."""
    ok = (f["dominant_k"] >= 8 and f["tooth_strength"] >= 0.015 and
          f["tooth_purity"] >= 0.2 and f["solidity"] >= 0.85 and f["elongation"] < 0.08)
    return GEAR if ok else NON_GEAR


def find_objects(img_bgr, min_area_frac=0.002):
    """Every plausible object in an image: contour, bbox, cropped-flag, features, geometry."""
    h, w = img_bgr.shape[:2]
    solid = segment_foreground(img_bgr)
    out = []
    for part in split_touching(solid):
        contours, _ = cv2.findContours(part, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            continue
        cnt = max(contours, key=cv2.contourArea)
        if cv2.contourArea(cnt) < max(400, min_area_frac * h * w):
            continue                                        # specks / watermark text
        x, y, bw, bh = cv2.boundingRect(cnt)
        m = 3
        cropped = x <= m or y <= m or x + bw >= w - m or y + bh >= h - m
        feats, geom = extract_features(cnt)
        if feats is None:
            continue
        out.append({"cnt": cnt, "bbox": (x, y, bw, bh), "cropped": cropped,
                    "features": feats, "geom": geom})
    out.sort(key=lambda o: -o["geom"]["area_px"])
    return out


# ===========================================================================
# 3. SYNTHETIC TRAINING DATA - generate thousands of labelled shapes so the
#    Random Forest has real variety to learn from, instead of copying its own
#    earlier guesses (which is what made the old model useless).
# ===========================================================================
SS = 4  # supersampling factor for smooth, anti-aliased silhouette edges


def _gear_points(rng, R, N):
    depth = np.clip(rng.uniform(3.6, 5.6) / N, 0.03, 0.30)
    f_root, f_flank = rng.uniform(0.28, 0.48), rng.uniform(0.08, 0.2)
    f_tip = 1.0 - f_root - 2 * f_flank
    if f_tip < 0.08:
        f_tip, f_root = 0.08, 1.0 - 0.08 - 2 * f_flank
    fr = np.cumsum([0, f_root, f_flank, f_tip, f_flank])
    rad = [R * (1 - depth), R * (1 - depth), R, R, R * (1 - depth)]
    pts, phase = [], rng.uniform(0, 2 * np.pi)
    step = 2 * np.pi / N
    for i in range(N):
        for f, r in zip(fr, rad):
            a = phase + (i + f) * step
            pts.append((r * np.cos(a), r * np.sin(a)))
    return np.array(pts)


def _polar(theta, r):
    return np.stack([r * np.cos(theta), r * np.sin(theta)], axis=1)


def _regular_polygon(rng, R, n):
    ph = rng.uniform(0, 2 * np.pi)
    a = ph + np.arange(n) * 2 * np.pi / n
    return _polar(a, np.full(n, R))


def _star(rng, R, n):
    a = rng.uniform(0, 2 * np.pi) + np.arange(2 * n) * np.pi / n
    r = np.where(np.arange(2 * n) % 2 == 0, R, R * rng.uniform(0.25, 0.75))
    return _polar(a, r)


def _blob(rng, R):
    th = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    r = np.ones_like(th)
    for j in range(1, 7):
        r += rng.uniform(0, 0.28 / j) * np.cos(j * th + rng.uniform(0, 6.28))
    return _polar(th, R * r / r.max())


def _ellipse(rng, R):
    th = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    q = rng.uniform(0.35, 1.0)
    return np.stack([R * np.cos(th), R * q * np.sin(th)], axis=1)


def _rect(rng, R):
    q = rng.uniform(0.15, 1.0)
    return np.array([[-R, -R * q], [R, -R * q], [R, R * q], [-R, R * q]])


def _sector_window(rng, R):
    a0, span = rng.uniform(0, 6.28), rng.uniform(0.5, 1.5)
    r_in, r_out = R * rng.uniform(0.15, 0.45), R * rng.uniform(0.6, 1.0)
    ta = np.linspace(a0, a0 + span, 40)
    outer = _polar(ta, np.full(40, r_out))
    inner = _polar(ta[::-1], np.full(40, r_in))
    return np.vstack([outer, inner])


def _triangle_window(rng, R):
    return _regular_polygon(rng, R, 3) * np.array([1, rng.uniform(0.6, 1.0)])


def _bolt(rng, R):
    hexa = _regular_polygon(rng, R * 0.45, 6) + np.array([-R * 0.55, 0])
    body = np.array([[-R * 0.2, -R * 0.15], [R, -R * 0.15], [R, R * 0.15], [-R * 0.2, R * 0.15]])
    return hexa, body


def _draw(polys, size, rng, rotate=True):
    big = size * SS
    canvas = np.zeros((big, big), np.uint8)
    ang = rng.uniform(0, 2 * np.pi) if rotate else 0.0
    c, s = np.cos(ang), np.sin(ang)
    rot = np.array([[c, -s], [s, c]])
    for p in polys:
        q = (p @ rot.T) * SS + big / 2
        cv2.fillPoly(canvas, [np.round(q).astype(np.int32)], 255)
    small = cv2.resize(canvas, (size, size), interpolation=cv2.INTER_AREA)
    sigma = rng.uniform(0.3, 1.6)
    small = cv2.GaussianBlur(small, (0, 0), sigma)
    return (small > rng.uniform(100, 155)).astype(np.uint8) * 255


def make_sample(rng, want_gear):
    size = int(rng.integers(120, 420))
    R = rng.uniform(0.30, 0.46) * size
    if want_gear:
        n = int(rng.integers(8, 121))
        polys = [_gear_points(rng, R, n)]
        if rng.random() < 0.3:                            # slightly squashed by camera angle
            polys = [polys[0] * np.array([1, rng.uniform(0.9, 1.0)])]
    else:
        kind = rng.choice(["circle", "poly", "star", "blob", "ellipse", "rect", "sector",
                           "tri", "bolt", "cog", "wavy"],
                          p=[.08, .12, .1, .12, .1, .08, .14, .1, .05, .06, .05])
        if kind == "circle":
            polys = [_polar(np.linspace(0, 6.283, 300, endpoint=False), np.full(300, R))]
        elif kind == "poly":
            polys = [_regular_polygon(rng, R, int(rng.integers(3, 13)))]
        elif kind == "star":
            polys = [_star(rng, R, int(rng.integers(3, 13)))]
        elif kind == "blob":
            polys = [_blob(rng, R)]
        elif kind == "ellipse":
            polys = [_ellipse(rng, R)]
        elif kind == "rect":
            polys = [_rect(rng, R)]
        elif kind == "sector":
            polys = [_sector_window(rng, R)]
        elif kind == "tri":
            polys = [_triangle_window(rng, R)]
        elif kind == "bolt":
            polys = list(_bolt(rng, R))
        elif kind == "cog":                                # chunky wheel, too few teeth to be a gear
            polys = [_gear_points(rng, R, int(rng.integers(3, 8)))]
        else:                                               # barely-wavy circle, no real teeth
            th = np.linspace(0, 6.283, 720, endpoint=False)
            kk = int(rng.integers(8, 40))
            polys = [_polar(th, R * (1 + rng.uniform(0.0, 0.008) * np.cos(kk * th)))]
    mask = _draw(polys, size, rng)
    mask = cv2.copyMakeBorder(mask, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=0)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return None
    cnt = max(contours, key=cv2.contourArea)
    feats, _ = extract_features(cnt)
    return feats


def build_dataset(n_per_class=3000, seed=42):
    rng = np.random.default_rng(seed)
    X, y = [], []
    for want_gear in (True, False):
        got = 0
        while got < n_per_class:
            f = make_sample(rng, want_gear)
            if f is None:
                continue
            X.append([f[n] for n in FEATURE_NAMES])
            y.append(GEAR if want_gear else NON_GEAR)
            got += 1
    return np.array(X), np.array(y)


# ===========================================================================
# 4. TRAINING
# ===========================================================================
def _norm_label(s):
    s = str(s).strip().lower()
    if s.startswith("gear") or s.startswith("spur"):
        return GEAR
    if s.startswith("non"):
        return NON_GEAR
    return None


def learn_from_review(review_csv):
    """Fold your corrections in review_me.csv into the real-examples file."""
    import pandas as pd
    df = pd.read_csv(review_csv)
    if "true_label" not in df.columns:
        print("That CSV has no 'true_label' column - is it the right file?")
        return
    df["label"] = df["true_label"].map(lambda v: _norm_label(v) if pd.notna(v) else None)
    df = df[df["label"].notna()]
    if df.empty:
        print("No rows with a filled-in 'true_label' column found. "
              "Open review_me.csv, put 'Gear' or 'Non-Gear' next to the rows you checked, save, and rerun.")
        return
    keep = ["filename", "cx", "cy"] + FEATURE_NAMES + ["label"]
    df = df[keep]
    os.makedirs(os.path.dirname(REAL_PATH), exist_ok=True)
    if os.path.exists(REAL_PATH):
        old = pd.read_csv(REAL_PATH)
        df = pd.concat([old, df])
    df["cx"], df["cy"] = df["cx"].round(0), df["cy"].round(0)
    df = df.drop_duplicates(subset=["filename", "cx", "cy"], keep="last")
    df.to_csv(REAL_PATH, index=False)
    print(f"Saved {len(df)} verified real examples to {REAL_PATH}")


def train(n_per_class=3000, verbose=True):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
    import joblib

    X_syn, y_syn = build_dataset(n_per_class)
    w_syn = np.ones(len(y_syn))

    X_real = y_real = None
    if os.path.exists(REAL_PATH):
        import pandas as pd
        real = pd.read_csv(REAL_PATH)
        if len(real) >= 4:
            X_real, y_real = real[FEATURE_NAMES].values, real["label"].values

    clf_kwargs = dict(n_estimators=400, min_samples_leaf=2, max_features="sqrt",
                      class_weight="balanced", n_jobs=-1, random_state=42)

    if verbose:
        Xtr, Xte, ytr, yte = train_test_split(X_syn, y_syn, test_size=0.2,
                                              stratify=y_syn, random_state=42)
        probe = RandomForestClassifier(**clf_kwargs).fit(Xtr, ytr)
        print("\n=== Hold-out test (20% of synthetic data, model has never seen it) ===")
        print(classification_report(yte, probe.predict(Xte), digits=3))
        print("Confusion matrix [rows=true, cols=predicted], order:", list(probe.classes_))
        print(confusion_matrix(yte, probe.predict(Xte), labels=probe.classes_))
        cv = cross_val_score(RandomForestClassifier(**clf_kwargs), X_syn, y_syn,
                             cv=StratifiedKFold(5, shuffle=True, random_state=1))
        print(f"5-fold cross-validation accuracy: {cv.mean():.3f} +/- {cv.std():.3f}")
        if X_real is not None:
            pr = probe.predict(X_real)
            print(f"\n=== Your verified real examples ({len(y_real)}) ===")
            print(f"Accuracy of a synthetic-only model on them: {(pr == y_real).mean():.3f}")

    X, y, w = X_syn, y_syn, w_syn
    if X_real is not None:
        X = np.vstack([X_syn, X_real])
        y = np.concatenate([y_syn, y_real])
        w = np.concatenate([w_syn, np.full(len(y_real), REAL_WEIGHT)])
    clf = RandomForestClassifier(**clf_kwargs).fit(X, y, sample_weight=w)

    if verbose:
        print("\nFeature importance (what the model actually leans on):")
        for n, imp in sorted(zip(FEATURE_NAMES, clf.feature_importances_), key=lambda t: -t[1]):
            print(f"  {n:15s} {imp:.3f}")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")
    return clf


def load_or_train(force_retrain=False):
    import joblib
    if not force_retrain and os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    print("Training the model now - this takes about 30-60 seconds, one time only...")
    return train(verbose=True)


# ===========================================================================
# 5. BATCH INSPECTION
# ===========================================================================
def list_images(folder):
    files = []
    for ext in IMG_EXTS:
        files += glob.glob(os.path.join(folder, f"*.{ext}"))
        files += glob.glob(os.path.join(folder, f"*.{ext.upper()}"))
    return sorted(set(files))


def predict(clf, feats):
    x = np.array([[feats[n] for n in FEATURE_NAMES]])
    if clf is None:
        return rule_based_label(feats), 1.0
    proba = clf.predict_proba(x)[0]
    i = int(np.argmax(proba))
    return str(clf.classes_[i]), float(proba[i])


def find_meshing_pairs(gears):
    """Two gears mesh when their centre distance is close to the sum of their pitch radii."""
    pairs = []
    for i in range(len(gears)):
        for j in range(i + 1, len(gears)):
            a, b = gears[i], gears[j]
            d = np.hypot(a["cx"] - b["cx"], a["cy"] - b["cy"])
            expect = a["pitch_radius_px"] + b["pitch_radius_px"]
            if expect > 0 and 0.85 <= d / expect <= 1.15:
                ratio_teeth = a["tooth_count"] / b["tooth_count"]
                ratio_geom = a["pitch_radius_px"] / b["pitch_radius_px"]
                pairs.append({
                    "gear_a": a["id"], "gear_b": b["id"],
                    "centre_distance_px": round(float(d), 1),
                    "ratio_a_to_b_from_teeth": round(ratio_teeth, 4),
                    "ratio_a_to_b_from_radii": round(ratio_geom, 4),
                    "consistent": bool(abs(ratio_teeth / ratio_geom - 1) < 0.2),
                })
    return pairs


def annotate(img, obj, label, conf, idx):
    cnt, (x, y, w, h) = obj["cnt"], obj["bbox"]
    if obj["cropped"]:
        color, text = (0, 165, 255), f"#{idx} cropped at border"
    elif conf < UNSURE_BELOW:
        color, text = (0, 220, 255), f"#{idx} unsure? {label.split(' ')[0]} {conf:.0%}"
    elif label == GEAR:
        color, text = (0, 200, 0), f"#{idx} Gear {obj['geom']['tooth_count']}T {conf:.0%}"
    else:
        color, text = (0, 0, 255), f"#{idx} Non-gear {conf:.0%}"
    cv2.drawContours(img, [cnt], -1, color, 2)
    if label == GEAR and not obj["cropped"]:
        cx, cy = int(obj["geom"]["cx"]), int(obj["geom"]["cy"])
        cv2.drawMarker(img, (cx, cy), color, cv2.MARKER_CROSS, 14, 2)
    scale = max(0.45, min(img.shape[:2]) / 900)
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
    ty = max(th + 6, y - 6)
    cv2.rectangle(img, (x, ty - th - 6), (x + tw + 8, ty + 4), (0, 0, 0), -1)
    cv2.putText(img, text, (x + 4, ty), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2)


def inspect(image_dir, output_dir, force_retrain=False):
    os.makedirs(output_dir, exist_ok=True)
    files = list_images(image_dir)
    if not files:
        print(f"No images found in: {image_dir}")
        print(f"(looked for {', '.join(IMG_EXTS)} files)")
        return
    clf = load_or_train(force_retrain)
    print(f"\nInspecting {len(files)} image(s) from {image_dir}\n")

    header = (["filename", "object_id", "cx", "cy"] + FEATURE_NAMES +
              ["tooth_count", "tip_radius_px", "root_radius_px", "pitch_radius_px",
               "classification", "confidence", "status", "true_label"])
    rows, params = [], {}

    for path in files:
        name = os.path.basename(path)
        img = cv2.imread(path)
        if img is None:
            print(f"  ! could not read {name}")
            continue
        annotated = img.copy()
        objs = find_objects(img)
        gears = []
        for i, obj in enumerate(objs, start=1):
            f, g = obj["features"], obj["geom"]
            label, conf = predict(clf, f)
            status = ("cropped" if obj["cropped"] else
                      "unsure" if conf < UNSURE_BELOW else "ok")
            annotate(annotated, obj, label, conf, i)
            rows.append([name, i, round(g["cx"], 1), round(g["cy"], 1)] +
                        [round(f[n], 5) for n in FEATURE_NAMES] +
                        [g["tooth_count"], round(g["tip_radius_px"], 2), round(g["root_radius_px"], 2),
                         round(g["pitch_radius_px"], 2), label, round(conf, 3), status, ""])
            if label == GEAR and not obj["cropped"]:
                gears.append({"id": i, "cx": round(g["cx"], 1), "cy": round(g["cy"], 1),
                              "tooth_count": g["tooth_count"],
                              "tip_radius_px": round(g["tip_radius_px"], 1),
                              "root_radius_px": round(g["root_radius_px"], 1),
                              "pitch_radius_px": round(g["pitch_radius_px"], 1),
                              "confidence": round(conf, 3)})
        params[name] = {"image_size_px": [img.shape[1], img.shape[0]], "gears": gears,
                        "meshing_pairs": find_meshing_pairs(gears)}
        cv2.imwrite(os.path.join(output_dir, f"result_{name}"), annotated)
        print(f"  {name}: {len(objs)} object(s), {len(gears)} gear(s)"
              + "".join(f"  [#{g['id']}: {g['tooth_count']} teeth]" for g in gears))

    for fname in ("inspection_summary.csv", "review_me.csv"):
        with open(os.path.join(output_dir, fname), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(rows)
    with open(os.path.join(output_dir, "gear_params.json"), "w") as fh:
        json.dump(params, fh, indent=2)
    print(f"\nDone. Results in {output_dir}/")
    print("  - inspection_summary.csv  (every object + measurements + prediction)")
    print("  - review_me.csv           (correct this, then run --learn on it)")
    print("  - gear_params.json        (centres/radii/tooth counts/ratios -> for MATLAB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--images", default=os.path.join(HERE, "images"))
    ap.add_argument("--out", default=os.path.join(HERE, "Sample_testing"))
    ap.add_argument("--retrain", action="store_true", help="retrain the model from scratch")
    ap.add_argument("--learn", metavar="REVIEW_CSV",
                    help="fold corrected labels from a review_me.csv into training, then retrain")
    a = ap.parse_args()
    if a.learn:
        learn_from_review(a.learn)
        train(verbose=True)
    else:
        inspect(a.images, a.out, force_retrain=a.retrain)
