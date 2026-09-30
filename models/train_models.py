"""
Offline training script — run once locally to produce:
  models/diabetes_model.pkl
  models/cardio_model.pkl
  models/model_metadata.json
"""

import os
import json
import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent   # project root
MODELS_DIR = Path(__file__).resolve().parent

# CSVs may live in data/ or at the project root (support both)
def _csv(name: str) -> Path:
    candidate = ROOT / "data" / name
    if candidate.exists():
        return candidate
    return ROOT / name


# ---------------------------------------------------------------------------
# Model 1 — Diabetes
# ---------------------------------------------------------------------------
def train_diabetes():
    print("\n=== Training Diabetes Model ===")
    df = pd.read_csv(_csv("diabetes.csv"))

    # Replace biologically-impossible zeros with NaN so the imputer fills them
    zero_cols = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]
    df[zero_cols] = df[zero_cols].replace(0, np.nan)

    features = [
        "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
        "Insulin", "BMI", "DiabetesPedigreeFunction", "Age",
    ]
    X = df[features].values
    y = df["Outcome"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
        ("clf",     RandomForestClassifier(n_estimators=100, random_state=42)),
    ])

    pipeline.fit(X_train, y_train)

    y_pred  = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    acc     = accuracy_score(y_test, y_pred)
    auc     = roc_auc_score(y_test, y_proba)
    cv_acc  = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy").mean()

    print(f"  Accuracy : {acc:.4f}")
    print(f"  ROC-AUC  : {auc:.4f}")
    print(f"  CV Acc   : {cv_acc:.4f}  (5-fold)")

    out_path = MODELS_DIR / "diabetes_model.pkl"
    joblib.dump(pipeline, out_path)
    print(f"  Saved -> {out_path}")

    return {
        "accuracy":        round(float(acc),    4),
        "roc_auc":         round(float(auc),    4),
        "cv_accuracy_mean": round(float(cv_acc), 4),
        "train_samples":   int(len(X_train)),
        "test_samples":    int(len(X_test)),
        "features":        features,
        "trained_date":    datetime.date.today().isoformat(),
    }


# ---------------------------------------------------------------------------
# Model 2 — Cardiovascular
# ---------------------------------------------------------------------------
def _load_cardio_train() -> pd.DataFrame:
    df = pd.read_csv(_csv("cardio_train.csv"), sep=";")
    df["age"] = df["age"] / 365.25
    df["BMI"] = df["weight"] / (df["height"] / 100) ** 2
    keep = ["age", "gender", "BMI", "ap_hi", "ap_lo",
            "cholesterol", "gluc", "smoke", "alco", "active", "cardio"]
    return df[keep]


def _load_healthcare_synthetic() -> pd.DataFrame:
    df = pd.read_csv(_csv("healthcare_synthetic_data.csv"))

    # Ordinal cholesterol encoding
    chol = df["Cholesterol_Total"]
    df["cholesterol"] = np.where(chol < 200, 1, np.where(chol < 240, 2, 3))

    # Ordinal glucose encoding
    gluc = df["Fasting_Blood_Sugar"]
    df["gluc"] = np.where(gluc < 100, 1, np.where(gluc < 126, 2, 3))

    rename = {
        "Age":                    "age",
        "Gender":                 "gender",
        "BMI":                    "BMI",
        "Systolic_BP":            "ap_hi",
        "Diastolic_BP":           "ap_lo",
        "Smoking_Status":         "smoke",
        "Alcohol_Consumption":    "alco",
        "Physical_Activity_Level": "active",
        "Heart_Disease_Risk":     "cardio",
    }
    df = df.rename(columns=rename)
    keep = ["age", "gender", "BMI", "ap_hi", "ap_lo",
            "cholesterol", "gluc", "smoke", "alco", "active", "cardio"]
    return df[keep]


def train_cardio():
    print("\n=== Training Cardiovascular Model ===")

    df_cardio  = _load_cardio_train()
    df_synth   = _load_healthcare_synthetic()
    df         = pd.concat([df_cardio, df_synth], ignore_index=True)

    features = ["age", "gender", "BMI", "ap_hi", "ap_lo",
                "cholesterol", "gluc", "smoke", "alco", "active"]
    X = df[features].values
    y = df["cardio"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
        ("clf",     GradientBoostingClassifier(n_estimators=100, random_state=42)),
    ])

    pipeline.fit(X_train, y_train)

    y_pred  = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    acc     = accuracy_score(y_test, y_pred)
    auc     = roc_auc_score(y_test, y_proba)

    print(f"  Accuracy : {acc:.4f}")
    print(f"  ROC-AUC  : {auc:.4f}")

    out_path = MODELS_DIR / "cardio_model.pkl"
    joblib.dump(pipeline, out_path)
    print(f"  Saved -> {out_path}")

    return {
        "accuracy":      round(float(acc), 4),
        "roc_auc":       round(float(auc), 4),
        "train_samples": int(len(X_train)),
        "test_samples":  int(len(X_test)),
        "features":      features,
        "trained_date":  datetime.date.today().isoformat(),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    diabetes_meta = train_diabetes()
    cardio_meta   = train_cardio()

    metadata = {
        "diabetes":       diabetes_meta,
        "cardiovascular": cardio_meta,
    }

    meta_path = MODELS_DIR / "model_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\n=== Metadata saved -> {meta_path} ===")
    print(json.dumps(metadata, indent=2))
