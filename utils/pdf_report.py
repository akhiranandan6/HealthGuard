"""PDF report generation for the Health Risk Assessment Dashboard.

Uses fpdf2 (pure Python) with built-in Helvetica font only — no external TTF
files, so the report works on Streamlit Community Cloud.

Usage:
    from utils.pdf_report import generate_pdf
    pdf_bytes = generate_pdf(record)   # record from st.session_state["history"]
    st.download_button(..., data=pdf_bytes, mime="application/pdf")
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from fpdf import FPDF

from utils.recommendations import get_recommendations

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_META_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "model_metadata.json",
)

_ACTIVITY_LABELS = {
    0: "Sedentary",
    1: "Lightly Active",
    2: "Moderately Active",
    3: "Very Active",
}

# Colour tuples for risk categories
_RISK_COLORS = {
    "Low": {
        "fill": (220, 252, 231),   # light green
        "text": (22, 101, 52),     # dark green
        "label": "[LOW RISK]",
    },
    "Moderate": {
        "fill": (254, 249, 195),   # light yellow
        "text": (133, 77, 14),     # dark amber
        "label": "[MODERATE RISK]",
    },
    "High": {
        "fill": (254, 226, 226),   # light red
        "text": (153, 27, 27),     # dark red
        "label": "[HIGH RISK]",
    },
}

_PRIORITY_PREFIX = {"High": "[HIGH]", "Medium": "[MEDIUM]", "Low": "[LOW]"}
_CATEGORY_ORDER = ["Diet", "Exercise", "Checkup", "Lifestyle"]

# Characters that Helvetica (latin-1) cannot encode — map to ASCII equivalents
_UNICODE_MAP = str.maketrans({
    "\u2013": "-",   # en-dash
    "\u2014": "--",  # em-dash
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u2026": "...", # ellipsis
    "\u00b0": " degrees",  # degree sign
    "\u00e9": "e",   # e-acute
    "\u00e0": "a",   # a-grave
    "\u00fc": "u",   # u-umlaut
    "\u00f6": "o",   # o-umlaut
    "\u00e4": "a",   # a-umlaut
    "\u00b1": "+/-", # plus-minus
    "\u00d7": "x",   # multiplication
    "\u2192": "->",  # right arrow
    "\u2022": "-",   # bullet
    "\u00a0": " ",   # non-breaking space
})


def _safe(text: str) -> str:
    """Sanitise text so it encodes cleanly in Helvetica (latin-1)."""
    text = text.translate(_UNICODE_MAP)
    # Drop any remaining non-latin-1 characters
    return text.encode("latin-1", errors="replace").decode("latin-1")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def _load_metadata() -> dict:
    try:
        with open(_META_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ---------------------------------------------------------------------------
# PDF builder helpers
# ---------------------------------------------------------------------------

def _section_heading(pdf: FPDF, text: str) -> None:
    """Full-width blue section heading bar with white text."""
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, _safe(text), new_x="LMARGIN", new_y="NEXT", fill=True, align="L")
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)


def _table_row(pdf: FPDF, label: str, value: str, shade: bool = False) -> None:
    """Two-column table row with optional light shading."""
    if shade:
        pdf.set_fill_color(247, 248, 250)
    else:
        pdf.set_fill_color(255, 255, 255)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(65, 7, _safe(label), border=1, fill=shade, align="L")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 7, _safe(str(value)), border=1, fill=shade, new_x="LMARGIN", new_y="NEXT", align="L")


def _score_row(pdf: FPDF, label: str, value: str, bold_label: bool = False) -> None:
    """Score breakdown row."""
    if bold_label:
        pdf.set_font("Helvetica", "B", 9)
    else:
        pdf.set_font("Helvetica", "", 9)
    pdf.cell(100, 7, _safe(label), border=1, align="L")
    pdf.set_font("Helvetica", "B" if bold_label else "", 9)
    pdf.cell(0, 7, _safe(value), border=1, new_x="LMARGIN", new_y="NEXT", align="C")


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_pdf(record: dict) -> bytes:
    """Generate a PDF risk report and return it as bytes.

    Parameters
    ----------
    record:
        A session history entry with keys:
        ``timestamp``, ``inputs``, ``diabetes``, ``cardio``.
    """
    inputs: dict = record.get("inputs", {})
    diabetes: dict = record.get("diabetes", {})
    cardio: dict = record.get("cardio", {})
    timestamp: str = record.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    pdf = FPDF("P", "mm", "A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 10, 15)

    # -----------------------------------------------------------------------
    # 1. Header band
    # -----------------------------------------------------------------------
    pdf.set_fill_color(37, 99, 235)
    pdf.rect(0, 0, 210, 28, "F")

    pdf.set_xy(15, 7)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, "HEALTH RISK ASSESSMENT REPORT", align="L")

    pdf.set_xy(15, 17)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated on {timestamp}", align="L")

    pdf.set_text_color(0, 0, 0)
    pdf.set_y(34)

    # -----------------------------------------------------------------------
    # 2. Disclaimer box
    # -----------------------------------------------------------------------
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(
        0, 5,
        "WARNING: This report is for educational purposes only and does not constitute "
        "medical advice. Consult a qualified healthcare professional before making any "
        "health decisions.",
        border=1,
        fill=True,
        align="L",
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # -----------------------------------------------------------------------
    # 3. Patient Summary
    # -----------------------------------------------------------------------
    _section_heading(pdf, "  PATIENT SUMMARY")

    age = inputs.get("age", "N/A")
    gender_raw = inputs.get("gender", 1)
    gender = "Female" if gender_raw == 0 else "Male"
    height = inputs.get("height_cm", inputs.get("height", "N/A"))
    weight = inputs.get("weight_kg", inputs.get("weight", "N/A"))
    bmi = inputs.get("bmi", 0.0)
    bmi_cat = _bmi_category(float(bmi)) if bmi else "N/A"
    systolic = inputs.get("systolic_bp", "N/A")
    diastolic = inputs.get("diastolic_bp", "N/A")
    glucose = inputs.get("glucose", "N/A")
    cholesterol = inputs.get("cholesterol", "N/A")
    hdl = inputs.get("hdl", "N/A")
    smoking = "Yes" if inputs.get("smoking", 0) == 1 else "No"
    alcohol = "Yes" if inputs.get("alcohol", 0) == 1 else "No"
    activity_code = inputs.get("activity", 2)
    activity = _ACTIVITY_LABELS.get(int(activity_code), str(activity_code))
    family_history = "Yes" if inputs.get("family_history", 0) == 1 else "No"
    stress = inputs.get("stress", "N/A")
    sleep = inputs.get("sleep_hours", "N/A")

    rows = [
        ("Age", f"{age} years"),
        ("Gender", gender),
        ("Height", f"{height} cm"),
        ("Weight", f"{weight} kg"),
        ("BMI", f"{bmi:.1f} ({bmi_cat})" if isinstance(bmi, (int, float)) else str(bmi)),
        ("Blood Pressure", f"{systolic}/{diastolic} mmHg"),
        ("Fasting Glucose", f"{glucose} mg/dL"),
        ("Total Cholesterol", f"{cholesterol} mg/dL"),
        ("HDL Cholesterol", f"{hdl} mg/dL"),
        ("Smoking", smoking),
        ("Alcohol", alcohol),
        ("Physical Activity", activity),
        ("Family History (Diabetes/CVD)", family_history),
        ("Stress Level", f"{stress}/10"),
        ("Sleep Hours", f"{sleep} hrs/night"),
    ]

    for i, (label, value) in enumerate(rows):
        _table_row(pdf, label, value, shade=(i % 2 == 0))

    pdf.ln(5)

    # -----------------------------------------------------------------------
    # 4. Risk Scores
    # -----------------------------------------------------------------------
    _section_heading(pdf, "  RISK ASSESSMENT RESULTS")

    for disease_name, result in [("Diabetes", diabetes), ("Cardiovascular Disease", cardio)]:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(235, 242, 255)
        pdf.cell(0, 7, f"  {disease_name}", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(1)

        ml_prob = result.get("ml_prob", 0.0)
        formula_score = result.get("formula_score", 0.0)
        hybrid_score = result.get("hybrid_score", 0.0)
        category = result.get("category", "Low")

        _score_row(pdf, "ML Model Probability", f"{ml_prob:.1f}%")
        _score_row(pdf, "Clinical Formula Score", f"{formula_score:.1f}/100")
        _score_row(pdf, "HYBRID RISK SCORE (FINAL)", f"{hybrid_score:.1f}/100", bold_label=True)

        # Risk category coloured box
        risk_cfg = _RISK_COLORS.get(category, _RISK_COLORS["Low"])
        fr, fg, fb = risk_cfg["fill"]
        tr, tg, tb = risk_cfg["text"]
        pdf.ln(2)
        pdf.set_fill_color(fr, fg, fb)
        pdf.set_text_color(tr, tg, tb)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 9, risk_cfg["label"], new_x="LMARGIN", new_y="NEXT", fill=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

    # -----------------------------------------------------------------------
    # 5. Recommendations
    # -----------------------------------------------------------------------
    _section_heading(pdf, "  PERSONALISED RECOMMENDATIONS")

    recommendations = get_recommendations(inputs, diabetes, cardio)

    by_cat: dict[str, list] = {cat: [] for cat in _CATEGORY_ORDER}
    for rec in recommendations:
        if rec.category in by_cat:
            by_cat[rec.category].append(rec)

    counter = 1
    for cat in _CATEGORY_ORDER:
        cat_recs = by_cat[cat]
        if not cat_recs:
            continue

        # Category sub-heading
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(0, 6, f"  {cat.upper()}", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(1)

        for rec in cat_recs:
            prefix = _PRIORITY_PREFIX.get(rec.priority, rec.priority)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(22, 5, _safe(f"{counter}. {prefix}"), align="L")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5, _safe(rec.text), align="L")
            counter += 1
            pdf.ln(1)

        pdf.ln(2)

    # -----------------------------------------------------------------------
    # 6. Model Accuracy Disclosure
    # -----------------------------------------------------------------------
    _section_heading(pdf, "  MODEL ACCURACY DISCLOSURE")

    metadata = _load_metadata()

    dm = metadata.get("diabetes", {})
    cm_meta = metadata.get("cardiovascular", {})

    # Fallback values from the plan spec
    d_acc = dm.get("accuracy", 0.76)
    d_auc = dm.get("roc_auc", 0.83)
    d_n = dm.get("train_samples", 614)

    c_acc = cm_meta.get("accuracy", 0.73)
    c_auc = cm_meta.get("roc_auc", 0.80)
    c_n = cm_meta.get("train_samples", 67440)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(
        0, 5,
        f"Diabetes Model:        Accuracy {d_acc:.1%},  ROC-AUC {d_auc:.2f},  "
        f"trained on {d_n:,} samples\n"
        f"Cardiovascular Model:  Accuracy {c_acc:.1%},  ROC-AUC {c_auc:.2f},  "
        f"trained on {c_n:,} samples\n\n"
        "These scores are generated by machine learning models trained on population datasets. "
        "Results may not reflect your individual circumstances. Always consult a qualified "
        "healthcare professional for diagnosis, treatment, and medical advice.",
        align="L",
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # -----------------------------------------------------------------------
    # 7. Footer
    # -----------------------------------------------------------------------
    current_year = datetime.now().year
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(
        0, 6,
        f"Health Risk Assessment Dashboard  |  {current_year}  |  For informational purposes only",
        new_x="LMARGIN", new_y="NEXT",
        align="C",
    )

    return bytes(pdf.output())
