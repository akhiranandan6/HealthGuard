import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Assessment History — HealthGuard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);
            border-radius:14px;padding:2rem 2.2rem;color:white;margin-bottom:2rem;">
  <h2 style="color:white;font-size:1.9rem;font-weight:700;margin:0 0 0.3rem;">📈 Assessment History</h2>
  <p style="color:rgba(255,255,255,0.85);margin:0;">
    Track how your health risk scores change across assessments during this session.
  </p>
</div>
""", unsafe_allow_html=True)

st.info("ℹ️ **Session only:** History is stored in your browser session and will be cleared when you close or refresh the tab.")

history = st.session_state.get("history", [])

# ── Empty state ───────────────────────────────────────────────────────────────
if len(history) == 0:
    st.warning("No assessments yet. Complete your first health assessment to start tracking your progress.")
    if st.button("📋 Start Your First Assessment", type="primary"):
        st.switch_page("pages/1_Assessment.py")
    st.stop()

# ── Summary metrics ───────────────────────────────────────────────────────────
latest  = history[-1]
d_score = latest["diabetes"]["hybrid_score"]
d_cat   = latest["diabetes"]["category"]
c_score = latest["cardio"]["hybrid_score"]
c_cat   = latest["cardio"]["category"]
_CAT_ICON = {"Low": "🟢", "Moderate": "🟡", "High": "🔴"}

m1, m2, m3, m4 = st.columns(4, gap="medium")
with m1:
    st.metric("Total Assessments", len(history))
with m2:
    st.metric("Latest Diabetes Score", f"{d_score:.1f}", delta=f"{_CAT_ICON[d_cat]} {d_cat}")
with m3:
    st.metric("Latest CVD Score", f"{c_score:.1f}", delta=f"{_CAT_ICON[c_cat]} {c_cat}")
with m4:
    st.metric("Last Assessment", latest["timestamp"])

st.divider()

# ── Trend Chart ───────────────────────────────────────────────────────────────
if len(history) == 1:
    st.info("💡 Take another assessment to see your progress trend line.")

labels          = [f"#{i+1}  {r['timestamp']}" for i, r in enumerate(history)]
diabetes_scores = [r["diabetes"]["hybrid_score"] for r in history]
cardio_scores   = [r["cardio"]["hybrid_score"]   for r in history]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=labels, y=diabetes_scores, name="Diabetes Risk",
    mode="lines+markers", line=dict(color="#3b82f6", width=2.5), marker=dict(size=8),
    fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
))
fig.add_trace(go.Scatter(
    x=labels, y=cardio_scores, name="CVD Risk",
    mode="lines+markers", line=dict(color="#ef4444", width=2.5), marker=dict(size=8),
    fill="tozeroy", fillcolor="rgba(239,68,68,0.08)",
))
fig.add_hline(y=30, line_dash="dash", line_color="#16a34a", line_width=1.5,
              annotation_text="Low / Moderate (30)", annotation_position="top right",
              annotation_font=dict(size=11, color="#16a34a"))
fig.add_hline(y=60, line_dash="dash", line_color="#d97706", line_width=1.5,
              annotation_text="Moderate / High (60)", annotation_position="top right",
              annotation_font=dict(size=11, color="#d97706"))
fig.update_layout(
    title="Risk Score Trend Over Time",
    yaxis=dict(title="Risk Score (0–100)", range=[0, 100]),
    xaxis=dict(title="Assessment"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=420, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=60, b=40, l=10, r=10),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── History Table ─────────────────────────────────────────────────────────────
st.subheader("📋 All Assessments")

rows = []
for i, r in enumerate(history, start=1):
    inp = r.get("inputs", {})
    rows.append({
        "#": i, "Date / Time": r["timestamp"],
        "Age": inp.get("age", ""), "BMI": inp.get("bmi", ""),
        "Systolic BP": inp.get("systolic_bp", ""), "Glucose": inp.get("glucose", ""),
        "Diabetes Score": round(r["diabetes"]["hybrid_score"], 1),
        "Diabetes Risk":  r["diabetes"]["category"],
        "CVD Score":      round(r["cardio"]["hybrid_score"], 1),
        "CVD Risk":       r["cardio"]["category"],
    })

df = pd.DataFrame(rows)
st.dataframe(
    df, use_container_width=True, hide_index=True,
    column_config={
        "Diabetes Score": st.column_config.ProgressColumn("Diabetes Score", min_value=0, max_value=100, format="%.1f"),
        "CVD Score":      st.column_config.ProgressColumn("CVD Score",      min_value=0, max_value=100, format="%.1f"),
    },
)

# ── Clear History ─────────────────────────────────────────────────────────────
st.divider()
cl1, cl2 = st.columns([1, 5])

with cl1:
    if st.button("🗑️ Clear History", type="secondary"):
        st.session_state["confirm_clear"] = True

if st.session_state.get("confirm_clear"):
    with cl2:
        st.warning("⚠️ Are you sure? This will permanently delete all session assessments.")
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if st.button("Yes, clear all", type="primary"):
                st.session_state["history"] = []
                st.session_state["confirm_clear"] = False
                st.rerun()
        with c2:
            if st.button("Cancel"):
                st.session_state["confirm_clear"] = False
                st.rerun()

# ── Navigation ────────────────────────────────────────────────────────────────
st.divider()
nav1, nav2, _ = st.columns([1, 1, 3])
with nav1:
    if st.button("📋 New Assessment", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Assessment.py")
with nav2:
    if st.button("📊 View Latest Results", use_container_width=True, type="secondary"):
        st.switch_page("pages/2_Results.py")
