"""
utils/scoring.py — Hybrid Scoring Engine

Combines:
  (a) a clinical formula score (ADA diabetes / Framingham CVD)
  (b) the ML model probability (loaded from models/*.pkl)

into a single 0–100 hybrid risk score with a Low/Moderate/High label.

Importable standalone (no Streamlit dependency).  Models are loaded once per
process and cached in the module-level _MODELS dict.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

import joblib
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

# Module-level singleton cache  {name: pipeline}
_MODELS: dict = {}


def _load_model(name: str):
    """Load and cache a model by filename (without .pkl extension)."""
    if name not in _MODELS:
        path = _MODELS_DIR / f"{name}.pkl"
        _MODELS[name] = joblib.load(path)
    return _MODELS[name]


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------
class ScoringResult(TypedDict):
    ml_prob: float        # 0-100  ML model probability %
    formula_score: float  # 0-100  clinical formula score
    hybrid_score: float   # 0-100  combined score
    category: str         # "Low" | "Moderate" | "High"
    category_color: str   # "green" | "orange" | "red"


def _categorise(score: float) -> tuple[str, str]:
    if score < 30:
        return "Low", "green"
    if score < 60:
        return "Moderate", "orange"
    return "High", "red"


# ---------------------------------------------------------------------------
# ADA Diabetes Formula  (simplified ADA Risk Test, 0–100 scale)
# Max raw points = 19
# ---------------------------------------------------------------------------
def _ada_diabetes_formula(inp: dict) -> float:
    """
    Points-based ADA diabetes risk test.
    Returns a 0–100 normalised score.
    """
    points = 0

    # Age
    age = inp["age"]
    if age >= 60:
        points += 3
    elif age >= 50:
        points += 2
    elif age >= 40:
        points += 1

    # BMI
    bmi = inp["bmi"]
    if bmi >= 30:
        points += 3
    elif bmi >= 25:
        points += 1

    # Family history of diabetes
    if inp.get("family_history", 0):
        points += 5

    # Hypertension (systolic ≥ 130 OR diastolic ≥ 80)
    if inp["systolic_bp"] >= 130 or inp["diastolic_bp"] >= 80:
        points += 1

    # Physical inactivity (activity < 2)
    if inp["activity"] < 2:
        points += 1

    # Prior high glucose (fasting glucose > 100 mg/dL)
    if inp["glucose"] > 100:
        points += 5

    # Gestational history (pregnancies > 0 and female)
    if inp.get("pregnancies", 0) > 0 and inp.get("gender", 1) == 0:
        points += 1

    max_points = 19
    return round((points / max_points) * 100, 2)


# ---------------------------------------------------------------------------
# Framingham CVD Formula  (simplified ATP III 10-year risk, 0–100 scale)
# ---------------------------------------------------------------------------

# Framingham point-to-10yr-risk % lookup (ATP III; points → %)
# Covers from ≤-3 up to ≥18
_FRAMINGHAM_RISK_TABLE = {
    -3: 1, -2: 1, -1: 1, 0: 1,
    1: 1,  2: 1,  3: 1,  4: 1,
    5: 2,  6: 2,  7: 3,  8: 4,
    9: 5, 10: 6, 11: 8, 12: 10,
    13: 12, 14: 16, 15: 20, 16: 25,
    17: 30,
}
_FRAMINGHAM_MAX_RISK_SCORE = 30  # 30 % → 100 on our 0-100 scale


def _framingham_cvd_formula(inp: dict) -> float:
    """
    Simplified Framingham/ATP-III points system.
    Returns a 0–100 normalised score (30% 10-yr risk → 100).
    """
    points = 0
    age = inp["age"]
    gender = inp.get("gender", 1)  # 1=Male, 0=Female

    # --- Age ---
    if gender == 1:  # Male
        if age >= 75:   points += 15
        elif age >= 70: points += 14
        elif age >= 65: points += 12
        elif age >= 60: points += 11
        elif age >= 55: points += 10
        elif age >= 50: points += 8
        elif age >= 45: points += 6
        elif age >= 40: points += 5
        elif age >= 35: points += 2
        # 30-34 → 0
    else:  # Female
        if age >= 75:   points += 8
        elif age >= 70: points += 8
        elif age >= 65: points += 8
        elif age >= 60: points += 8
        elif age >= 55: points += 7
        elif age >= 50: points += 6
        elif age >= 45: points += 3
        elif age >= 40: points += 0
        elif age >= 35: points += -4
        else:           points += -9

    # --- Total Cholesterol (mg/dL) ---
    chol = inp["cholesterol"]
    if chol >= 280:
        points += 3
    elif chol >= 240:
        points += 2
    elif chol >= 200:
        points += 1
    # < 200 → 0

    # --- HDL (mg/dL) ---
    hdl = inp.get("hdl", 50)
    if hdl >= 60:
        points += -2
    elif hdl >= 50:
        points += 0
    elif hdl >= 40:
        points += 1
    else:
        points += 2

    # --- Systolic BP (untreated) ---
    sbp = inp["systolic_bp"]
    if sbp >= 160:
        points += 4
    elif sbp >= 140:
        points += 3
    elif sbp >= 130:
        points += 2
    elif sbp >= 120:
        points += 1
    # < 120 → 0

    # --- Smoking ---
    if inp.get("smoking", 0):
        points += 2

    # --- Diabetes (fasting glucose ≥ 126 mg/dL) ---
    if inp["glucose"] >= 126:
        points += 2

    # Map points to 10-year risk %
    clamped = max(-3, min(points, 17))
    risk_pct = _FRAMINGHAM_RISK_TABLE[clamped]
    if points > 17:
        risk_pct = 30  # ≥ 30% at top end

    # Scale to 0-100 (30% risk → 100)
    score = (risk_pct / _FRAMINGHAM_MAX_RISK_SCORE) * 100
    return round(min(score, 100.0), 2)


# ---------------------------------------------------------------------------
# Feature vector helpers
# ---------------------------------------------------------------------------

def _cholesterol_ordinal(chol_mgdl: float) -> int:
    """Map raw mg/dL to 1/2/3 ordinal matching cardio training data."""
    if chol_mgdl < 200:
        return 1
    if chol_mgdl < 240:
        return 2
    return 3


def _glucose_ordinal(gluc_mgdl: float) -> int:
    """Map raw mg/dL to 1/2/3 ordinal matching cardio training data."""
    if gluc_mgdl < 100:
        return 1
    if gluc_mgdl < 126:
        return 2
    return 3


def _diabetes_features(inp: dict) -> list:
    """
    Build the 8-element feature vector for the diabetes pipeline.
    Order: Pregnancies, Glucose, BloodPressure, SkinThickness,
           Insulin, BMI, DiabetesPedigreeFunction, Age
    """
    return [
        inp.get("pregnancies", 0),      # Pregnancies
        inp["glucose"],                  # Glucose
        inp["diastolic_bp"],             # BloodPressure (diastolic)
        20,                              # SkinThickness — median default
        80,                              # Insulin — median default
        inp["bmi"],                      # BMI
        0.5,                             # DiabetesPedigreeFunction — median default
        inp["age"],                      # Age
    ]


def _cardio_features(inp: dict) -> list:
    """
    Build the 10-element feature vector for the cardio pipeline.
    Order: age, gender, BMI, ap_hi, ap_lo, cholesterol, gluc, smoke, alco, active
    """
    return [
        inp["age"],
        inp.get("gender", 1),
        inp["bmi"],
        inp["systolic_bp"],                          # ap_hi
        inp["diastolic_bp"],                         # ap_lo
        _cholesterol_ordinal(inp["cholesterol"]),    # cholesterol ordinal
        _glucose_ordinal(inp["glucose"]),            # gluc ordinal
        inp.get("smoking", 0),                       # smoke
        inp.get("alcohol", 0),                       # alco
        inp.get("activity", 1),                      # active
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_diabetes(inputs: dict) -> ScoringResult:
    """
    Compute a hybrid diabetes risk score.

    Parameters
    ----------
    inputs : dict
        Flat input dict — see module docstring for schema.

    Returns
    -------
    ScoringResult
    """
    model = _load_model("diabetes_model")
    features = _diabetes_features(inputs)
    ml_prob = float(model.predict_proba([features])[0][1]) * 100

    formula_score = _ada_diabetes_formula(inputs)
    hybrid = round(0.6 * ml_prob + 0.4 * formula_score, 2)

    category, color = _categorise(hybrid)
    return ScoringResult(
        ml_prob=round(ml_prob, 2),
        formula_score=formula_score,
        hybrid_score=hybrid,
        category=category,
        category_color=color,
    )


def score_cardiovascular(inputs: dict) -> ScoringResult:
    """
    Compute a hybrid cardiovascular disease risk score.

    Parameters
    ----------
    inputs : dict
        Flat input dict — see module docstring for schema.

    Returns
    -------
    ScoringResult
    """
    model = _load_model("cardio_model")
    features = _cardio_features(inputs)
    ml_prob = float(model.predict_proba([features])[0][1]) * 100

    formula_score = _framingham_cvd_formula(inputs)
    hybrid = round(0.6 * ml_prob + 0.4 * formula_score, 2)

    category, color = _categorise(hybrid)
    return ScoringResult(
        ml_prob=round(ml_prob, 2),
        formula_score=formula_score,
        hybrid_score=hybrid,
        category=category,
        category_color=color,
    )
