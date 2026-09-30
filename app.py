import streamlit as st
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

st.set_page_config(
    page_title="HealthGuard — Risk Assessment Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "history" not in st.session_state:
    st.session_state["history"] = []

# ── Hero Banner ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 60%,#0ea5e9 100%);
            border-radius:16px;padding:3rem 2.5rem 2.5rem;color:white;margin-bottom:2rem;">
  <div style="display:inline-block;background:rgba(255,255,255,0.18);border:1px solid rgba(255,255,255,0.3);
              border-radius:20px;padding:3px 12px;font-size:0.78rem;font-weight:500;margin-bottom:1rem;
              letter-spacing:0.06em;text-transform:uppercase;">
    🔬 AI-Powered · Clinically Informed
  </div>
  <h1 style="font-size:2.4rem;font-weight:700;margin:0 0 0.5rem;color:white;">🏥 HealthGuard Risk Dashboard</h1>
  <p style="font-size:1.1rem;opacity:0.9;margin:0;line-height:1.7;">
    Enter your lifestyle and health data to instantly receive <strong>personalised risk scores</strong>
    for diabetes and cardiovascular disease — powered by machine learning and clinical formulas.
  </p>
  <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:1.5rem;">
    <span style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);
                 border-radius:8px;padding:0.5rem 1.1rem;font-size:0.85rem;font-weight:500;">📊 Diabetes &amp; CVD Risk</span>
    <span style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);
                 border-radius:8px;padding:0.5rem 1.1rem;font-size:0.85rem;font-weight:500;">🤖 86% Model Accuracy</span>
    <span style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);
                 border-radius:8px;padding:0.5rem 1.1rem;font-size:0.85rem;font-weight:500;">💡 Actionable Recommendations</span>
    <span style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);
                 border-radius:8px;padding:0.5rem 1.1rem;font-size:0.85rem;font-weight:500;">📄 Downloadable PDF Report</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Navigation Cards ──────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3, gap="large")

with c1:
    st.markdown("### 📋 Health Assessment")
    st.markdown("Enter age, weight, blood pressure, glucose, cholesterol, and lifestyle habits in one quick form.")
    st.page_link("pages/1_Assessment.py", label="Start Assessment →", icon="📋", use_container_width=True)

with c2:
    st.markdown("### 📊 Risk Results")
    st.markdown("Visual risk gauges, a score breakdown comparing ML vs clinical formula, and confidence disclosure.")
    st.page_link("pages/2_Results.py", label="View Results →", icon="📊", use_container_width=True)

with c3:
    st.markdown("### 📈 Progress History")
    st.markdown("Track how your risk scores trend across multiple assessments in this session.")
    st.page_link("pages/3_History.py", label="View History →", icon="📈", use_container_width=True)

# ── Disclaimer ────────────────────────────────────────────────────────────────
st.divider()
st.warning("⚠️ **Medical Disclaimer:** Risk scores are for **informational and educational purposes only**. They do not constitute medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional regarding your health.")
