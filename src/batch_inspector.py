"""
train_model.py - trains the gear Random Forest.

    python src/train_model.py
    python src/train_model.py --add src/Sample_testing/review_me.csv
"""
import argparse
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gear_core import FEATURE_NAMES, GEAR, NON_GEAR  # noqa: E402
from synth import build_dataset  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "models", "gear_rf.joblib")
REAL_PATH = os.path.join(HERE, "training_data", "real_labeled.csv")
REAL_WEIGHT = 10.0


def _norm_label(s):
    s = str(s).strip().lower()
    if s.startswith("gear") or s.startswith("spur"):
        return GEAR
    if s.startswith("non"):
        return NON_GEAR
    return None


def add_labels(review_csv):
    df = pd.read_csv(review_csv)
    df["label"] = df["true_label"].map(lambda v: _norm_label(v) if pd.notna(v) else None)
    df = df[df["label"].notna()]
    if df.empty:
        print("No rows with a filled 'true_label' column found.")
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
    X_syn, y_syn = build_dataset(n_per_class)
    w_syn = np.ones(len(y_syn))

    X_real = y_real = None
    if os.path.exists(REAL_PATH):
        real = pd.read_csv(REAL_PATH)
        X_real, y_real = real[FEATURE_NAMES].values, real["label"].values

    clf_kwargs = dict(n_estimators=400, min_samples_leaf=2, max_features="sqrt",
                      class_weight="balanced", n_jobs=-1, random_state=42)

    if verbose:
        Xtr, Xte, ytr, yte = train_test_split(X_syn, y_syn, test_size=0.2,
                                              stratify=y_syn, random_state=42)
        probe = RandomForestClassifier(**clf_kwargs).fit(Xtr, ytr)
        print("\n=== Hold-out test (20% of synthetic data) ===")
        print(classification_report(yte, probe.predict(Xte), digits=3))
        print("Confusion matrix [rows=true, cols=pred] order:", list(probe.classes_))
        print(confusion_matrix(yte, probe.predict(Xte), labels=probe.classes_))
        cv = cross_val_score(RandomForestClassifier(**clf_kwargs), X_syn, y_syn,
                             cv=StratifiedKFold(5, shuffle=True, random_state=1))
        print(f"5-fold CV accuracy: {cv.mean():.3f} +/- {cv.std():.3f}")
        if X_real is not None and len(y_real) >= 4:
            pr = probe.predict(X_real)
            print(f"\n=== Your verified REAL examples ({len(y_real)}) ===")
            print(f"Accuracy of synthetic-only model on them: {(pr == y_real).mean():.3f}")

    X, y, w = X_syn, y_syn, w_syn
    if X_real is not None:
        X = np.vstack([X_syn, X_real])
        y = np.concatenate([y_syn, y_real])
        w = np.concatenate([w_syn, np.full(len(y_real), REAL_WEIGHT)])
    clf = RandomForestClassifier(**clf_kwargs).fit(X, y, sample_weight=w)

    if verbose:
        print("\nFeature importance:")
        for n, imp in sorted(zip(FEATURE_NAMES, clf.feature_importances_), key=lambda t: -t[1]):
            print(f"  {n:15s} {imp:.3f}")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")
    return clf


def load_or_train():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    print("No trained model found - training one now (about 30 s)...")
    return train(verbose=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--add", help="review CSV with a filled 'true_label' column")
    args = ap.parse_args()
    if args.add:
        add_labels(args.add)
    train()