import streamlit as st
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.scoring import score_diabetes, score_cardiovascular

st.set_page_config(
    page_title="Health Assessment — HealthGuard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "history" not in st.session_state:
    st.session_state["history"] = []

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);
            border-radius:14px;padding:2rem 2.2rem;color:white;margin-bottom:2rem;">
  <h2 style="color:white;font-size:1.9rem;font-weight:700;margin:0 0 0.3rem;">📋 Health Risk Assessment</h2>
  <p style="color:rgba(255,255,255,0.85);margin:0;font-size:1rem;">
    Complete all sections below. Your data is used only for this session and never stored permanently.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Step indicators ───────────────────────────────────────────────────────────
p1, p2, p3 = st.columns(3)
for col, label in [(p1, "① Demographics"), (p2, "② Clinical Values"), (p3, "③ Lifestyle")]:
    with col:
        st.markdown(
            f'<div style="background:#2563eb;color:white;border-radius:8px;padding:0.5rem 1rem;'
            f'text-align:center;font-size:0.85rem;font-weight:600;">{label}</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Form ──────────────────────────────────────────────────────────────────────
with st.form("assessment_form", border=False):

    left, right = st.columns(2, gap="large")

    with left:
        st.subheader("① Demographics & Physical")

        age          = st.number_input("Age (years)", min_value=18, max_value=100, value=35, step=1)
        gender_label = st.selectbox("Gender", ["Female", "Male"])
        gender       = 0 if gender_label == "Female" else 1

        col_h, col_w = st.columns(2)
        with col_h:
            height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.5)
        with col_w:
            weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=70.0, step=0.5)

        _bmi = round(weight_kg / (height_cm / 100) ** 2, 1)
        _bmi_cat = ("Underweight" if _bmi < 18.5 else
                    "Normal weight" if _bmi < 25 else
                    "Overweight"    if _bmi < 30 else "Obese")
        st.info(f"**BMI: {_bmi}** — {_bmi_cat}")

        pregnancies    = st.number_input("Number of Pregnancies", min_value=0, max_value=20, value=0, step=1,
                                         help="Applicable for female patients. Enter 0 if not applicable.")
        family_history = st.checkbox("Family history of diabetes or heart disease")

    with right:
        st.subheader("② Clinical Values")

        bp1, bp2 = st.columns(2)
        with bp1:
            systolic_bp  = st.number_input("Systolic BP (mmHg)",  min_value=70,  max_value=250, value=120, step=1)
        with bp2:
            diastolic_bp = st.number_input("Diastolic BP (mmHg)", min_value=40,  max_value=150, value=80,  step=1)

        _bp_cat = ("Normal" if systolic_bp < 120 else
                   "Elevated" if systolic_bp < 130 else
                   "High Stage 1" if systolic_bp < 140 else "High Stage 2")
        st.caption(f"BP Status: {_bp_cat}")

        glucose = st.number_input("Fasting Blood Sugar (mg/dL)", min_value=50, max_value=500, value=90, step=1)
        _gl_cat = ("Normal" if glucose < 100 else "Pre-diabetic" if glucose < 126 else "Diabetic range")
        st.caption(f"Glucose: {_gl_cat}")

        ch1, ch2 = st.columns(2)
        with ch1:
            cholesterol = st.number_input("Total Cholesterol (mg/dL)", min_value=100, max_value=500, value=180, step=1)
        with ch2:
            hdl         = st.number_input("HDL Cholesterol (mg/dL)",   min_value=20,  max_value=150, value=50,  step=1)

    st.subheader("③ Lifestyle & Habits")
    ls1, ls2, ls3 = st.columns(3, gap="large")

    with ls1:
        smoking_label = st.radio("🚬 Smoking Status",     ["Non-smoker", "Smoker"])
        smoking       = 0 if smoking_label == "Non-smoker" else 1
        alcohol_label = st.radio("🍷 Alcohol Consumption", ["None / Occasional", "Regular"])
        alcohol       = 0 if alcohol_label == "None / Occasional" else 1

    with ls2:
        activity_label = st.select_slider(
            "🏃 Physical Activity Level",
            options=["Sedentary", "Lightly Active", "Moderately Active", "Very Active"],
            value="Lightly Active",
        )
        activity = {"Sedentary": 0, "Lightly Active": 1, "Moderately Active": 2, "Very Active": 3}[activity_label]
        stress   = st.slider("😓 Stress Level", 1, 10, 5, help="1 = Very low, 10 = Extremely high")

    with ls3:
        sleep_hours = st.slider("😴 Avg Sleep Hours / Night", 3.0, 12.0, 7.0, step=0.5)
        _sleep_cat  = "Good" if 7 <= sleep_hours <= 9 else ("Too little" if sleep_hours < 7 else "Too much")
        st.caption(f"Sleep: {_sleep_cat}")

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("⚡ Calculate My Risk Score", use_container_width=True, type="primary")

# ── Post-submit ───────────────────────────────────────────────────────────────
if submitted:
    bmi = round(weight_kg / (height_cm / 100) ** 2, 1)

    if glucose > 400:
        st.warning("⚠️ Glucose value seems very high — please verify.")
    if systolic_bp > 200:
        st.warning("⚠️ Systolic BP seems very high — please verify.")
    if bmi > 60:
        st.warning("⚠️ BMI seems unusually high — please verify height and weight.")
    if diastolic_bp >= systolic_bp:
        st.warning("⚠️ Diastolic BP should be lower than systolic BP.")

    inputs = {
        "age": int(age), "gender": gender, "bmi": bmi,
        "height_cm": float(height_cm), "weight_kg": float(weight_kg),
        "systolic_bp": int(systolic_bp), "diastolic_bp": int(diastolic_bp),
        "glucose": int(glucose), "cholesterol": int(cholesterol), "hdl": int(hdl),
        "smoking": smoking, "alcohol": alcohol, "activity": activity,
        "stress": stress, "sleep_hours": float(sleep_hours),
        "pregnancies": int(pregnancies), "family_history": int(family_history),
    }

    try:
        with st.spinner("🔬 Analysing your health data..."):
            diabetes_result = score_diabetes(inputs)
            cardio_result   = score_cardiovascular(inputs)
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "inputs": inputs, "diabetes": diabetes_result, "cardio": cardio_result,
        }
        st.session_state["history"].append(record)
        st.session_state["show_results"] = True
        st.switch_page("pages/2_Results.py")
    except Exception as exc:
        st.error(f"❌ Scoring failed: {exc}")
