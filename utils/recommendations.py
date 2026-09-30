"""Rule-based personalised recommendations engine.

Produces 4–8 actionable Recommendation objects sorted by priority
(High → Medium → Low) based on user inputs and risk-score results.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Recommendation:
    category: str   # "Diet" | "Exercise" | "Checkup" | "Lifestyle"
    priority: str   # "High" | "Medium" | "Low"
    icon: str       # emoji
    text: str       # actionable recommendation text


_PRIORITY_WEIGHT = {"High": 1, "Medium": 2, "Low": 3}

# Category icons
_ICON = {
    "Diet": "🥗",
    "Exercise": "🏃",
    "Checkup": "🩺",
    "Lifestyle": "💤",
}

# Default fallback recommendations (one per category, added when no rule fires)
_DEFAULTS = {
    "Diet": Recommendation(
        category="Diet",
        priority="Low",
        icon="🥗",
        text=(
            "Maintain a balanced diet rich in fruits, vegetables, whole grains, and lean "
            "proteins. Follow the Mediterranean or DASH dietary pattern for long-term health."
        ),
    ),
    "Exercise": Recommendation(
        category="Exercise",
        priority="Low",
        icon="🏃",
        text=(
            "Continue your current active lifestyle. Maintaining 150+ minutes of moderate "
            "exercise per week is one of the most powerful disease prevention strategies."
        ),
    ),
    "Lifestyle": Recommendation(
        category="Lifestyle",
        priority="Low",
        icon="💤",
        text=(
            "Stay hydrated (8 glasses of water/day), maintain social connections, and "
            "minimise screen time before bed."
        ),
    ),
}


def _diet_rules(inputs: dict) -> list[Recommendation]:
    recs: list[Recommendation] = []
    bmi = inputs.get("bmi", 0)
    glucose = inputs.get("glucose", 0)
    cholesterol = inputs.get("cholesterol", 0)
    hdl = inputs.get("hdl", 60)

    if bmi >= 30:
        recs.append(Recommendation("Diet", "High", "🥗",
            "Adopt a calorie-controlled diet. Aim to reduce daily intake by 500 kcal through "
            "smaller portions and avoiding processed foods. Target a BMI below 25."))
    elif bmi >= 25:
        recs.append(Recommendation("Diet", "Medium", "🥗",
            "Reduce refined carbohydrates and added sugars. Replace white bread/rice with "
            "whole-grain alternatives and increase vegetable intake to half your plate."))

    if glucose > 125:
        recs.append(Recommendation("Diet", "High", "🥗",
            "Follow a low-glycaemic index (low-GI) diet. Avoid sugary drinks, white rice, "
            "and processed snacks. Favour legumes, non-starchy vegetables, and lean proteins."))
    elif glucose >= 100:
        recs.append(Recommendation("Diet", "Medium", "🥗",
            "Limit foods that spike blood sugar. Reduce portion sizes of starchy foods and "
            "pair carbohydrates with protein or healthy fats to slow glucose absorption."))

    if cholesterol > 239:
        recs.append(Recommendation("Diet", "High", "🥗",
            "Reduce saturated fat and eliminate trans fats from your diet. Increase intake of "
            "omega-3 rich foods (salmon, walnuts, flaxseed) and soluble fibre (oats, beans)."))
    elif cholesterol >= 200:
        recs.append(Recommendation("Diet", "Medium", "🥗",
            "Limit red meat and full-fat dairy. Choose olive oil over butter and include plant "
            "sterols (found in fortified foods and nuts) to help lower LDL cholesterol."))

    if hdl < 40:
        recs.append(Recommendation("Diet", "Medium", "🥗",
            "Increase HDL ('good') cholesterol by consuming healthy fats (avocado, olive oil, "
            "nuts) and reducing refined carbohydrates."))

    return recs


def _exercise_rules(inputs: dict, diabetes_result: dict, cardio_result: dict) -> list[Recommendation]:
    recs: list[Recommendation] = []
    activity = inputs.get("activity", 2)
    bmi = inputs.get("bmi", 0)

    if activity == 0:
        recs.append(Recommendation("Exercise", "High", "🏃",
            "Begin with 30 minutes of brisk walking 5 days per week. Sedentary behaviour is a "
            "major risk factor for both diabetes and cardiovascular disease. Start slowly and "
            "increase gradually."))
    elif activity == 1:
        recs.append(Recommendation("Exercise", "Medium", "🏃",
            "Increase to at least 150 minutes of moderate aerobic exercise per week (e.g., "
            "cycling, swimming, fast walking). Add 2 strength-training sessions per week."))

    if (activity >= 2
            and (diabetes_result.get("hybrid_score", 0) > 50
                 or cardio_result.get("hybrid_score", 0) > 50)):
        recs.append(Recommendation("Exercise", "Medium", "🏃",
            "Maintain your current activity level. Consider adding high-intensity interval "
            "training (HIIT) 1–2 times per week to further reduce cardiovascular risk."))

    if bmi >= 30 and activity < 2:
        recs.append(Recommendation("Exercise", "High", "🏃",
            "Combine aerobic exercise with resistance training. Aim for 200–300 minutes of "
            "moderate activity per week to support weight loss alongside dietary changes."))

    return recs


def _checkup_rules(inputs: dict, diabetes_result: dict, cardio_result: dict) -> list[Recommendation]:
    recs: list[Recommendation] = []
    d_cat = diabetes_result.get("category", "Low")
    c_cat = cardio_result.get("category", "Low")
    age = inputs.get("age", 0)

    if d_cat == "High" or c_cat == "High":
        recs.append(Recommendation("Checkup", "High", "🩺",
            "Schedule a comprehensive health screening within the next 4–6 weeks. Request "
            "HbA1c, fasting lipid panel, ECG, and blood pressure monitoring from your doctor."))

    if d_cat == "Moderate" or c_cat == "Moderate":
        recs.append(Recommendation("Checkup", "Medium", "🩺",
            "Book a health check-up within 3 months. Ask your doctor for fasting glucose, "
            "HbA1c, and a full lipid panel. Aim for bi-annual reviews."))

    if d_cat == "Low" and c_cat == "Low":
        recs.append(Recommendation("Checkup", "Low", "🩺",
            "Maintain annual health check-ups even with low risk. Regular screening helps "
            "detect changes early. Include blood pressure, glucose, and cholesterol tests."))

    if age > 45 and (d_cat == "Moderate" or c_cat == "Moderate"):
        recs.append(Recommendation("Checkup", "High", "🩺",
            "Given your age and moderate risk, request a coronary calcium score (CACS) or "
            "stress test from your cardiologist as part of your next check-up."))

    return recs


def _lifestyle_rules(inputs: dict) -> list[Recommendation]:
    recs: list[Recommendation] = []
    smoking = inputs.get("smoking", 0)
    alcohol = inputs.get("alcohol", 0)
    stress = inputs.get("stress", 0)
    sleep_hours = inputs.get("sleep_hours", 7)
    systolic_bp = inputs.get("systolic_bp", 120)
    family_history = inputs.get("family_history", 0)

    if smoking == 1:
        recs.append(Recommendation("Lifestyle", "High", "💤",
            "Quit smoking immediately. Smoking doubles your cardiovascular risk and "
            "significantly increases diabetes complications. Speak to your doctor about "
            "nicotine replacement therapy or cessation programmes."))

    if alcohol == 1:
        recs.append(Recommendation("Lifestyle", "Medium", "💤",
            "Limit alcohol to no more than 1 unit per day (women) or 2 units (men). Excess "
            "alcohol raises blood pressure, triglycerides, and liver disease risk."))

    if stress > 7:
        recs.append(Recommendation("Lifestyle", "Medium", "💤",
            "Practice stress-reduction techniques daily: 10 minutes of mindfulness meditation, "
            "progressive muscle relaxation, or yoga. Chronic stress elevates cortisol, "
            "worsening blood sugar and blood pressure."))

    if sleep_hours < 6:
        recs.append(Recommendation("Lifestyle", "High", "💤",
            "Aim for 7–9 hours of sleep per night. Chronic sleep deprivation is linked to "
            "insulin resistance, weight gain, and elevated cardiovascular risk. Establish a "
            "consistent sleep schedule."))

    if sleep_hours > 9 and inputs.get("age", 0) < 60:
        recs.append(Recommendation("Lifestyle", "Low", "💤",
            "While rest is important, consistently sleeping over 9 hours may indicate an "
            "underlying issue. Discuss with your doctor if accompanied by fatigue."))

    if systolic_bp >= 130:
        recs.append(Recommendation("Lifestyle", "High", "💤",
            "Reduce dietary sodium to under 2,300 mg/day (about 1 teaspoon of salt). The DASH "
            "diet is clinically proven to lower blood pressure by 8–14 mmHg."))

    if family_history == 1:
        recs.append(Recommendation("Lifestyle", "Medium", "💤",
            "Given your family history, genetic risk factors are present. Early and regular "
            "screening is especially important. Inform your doctor of your family history for "
            "personalised prevention plans."))

    return recs


def get_recommendations(
    inputs: dict,
    diabetes_result: dict,
    cardio_result: dict,
) -> list[Recommendation]:
    """Return 4–8 sorted Recommendation objects for the given assessment."""
    all_recs: list[Recommendation] = []
    all_recs.extend(_diet_rules(inputs))
    all_recs.extend(_exercise_rules(inputs, diabetes_result, cardio_result))
    all_recs.extend(_checkup_rules(inputs, diabetes_result, cardio_result))
    all_recs.extend(_lifestyle_rules(inputs))

    # Ensure at least one recommendation per category
    present_categories = {r.category for r in all_recs}
    for category, default_rec in _DEFAULTS.items():
        if category not in present_categories:
            all_recs.append(default_rec)
    # Checkup default is always provided by the "Low risk" rule; no separate default needed.

    # Sort by priority weight (High=1, Medium=2, Low=3)
    all_recs.sort(key=lambda r: _PRIORITY_WEIGHT.get(r.priority, 3))

    # Cap at 8 — keep highest-priority items
    return all_recs[:8]
