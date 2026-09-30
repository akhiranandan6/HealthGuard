import streamlit as st
import plotly.graph_objects as go
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Risk Results — HealthGuard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

META_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "model_metadata.json",
)

@st.cache_data
def load_metadata() -> dict:
    try:
        with open(META_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# ── Helpers ───────────────────────────────────────────────────────────────────
_CAT_ICON  = {"Low": "🟢", "Moderate": "🟡", "High": "🔴"}
_COLOR_HEX = {"green": "#16a34a", "orange": "#d97706", "red": "#dc2626"}

def _gauge(title: str, score: float, color_key: str) -> go.Figure:
    hex_c = _COLOR_HEX.get(color_key, "#3b82f6")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"size": 17}},
        number={"suffix": "/100", "font": {"size": 38, "color": hex_c}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar":  {"color": hex_c, "thickness": 0.28},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30],   "color": "rgba(34,197,94,0.18)"},
                {"range": [30, 60],  "color": "rgba(234,179,8,0.18)"},
                {"range": [60, 100], "color": "rgba(239,68,68,0.18)"},
            ],
            "threshold": {"line": {"color": hex_c, "width": 3}, "thickness": 0.8, "value": score},
        },
    ))
    fig.update_layout(
        height=280, margin=dict(t=55, b=10, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def _badge(category: str) -> None:
    if category == "Low":
        st.success(f"🟢 LOW RISK")
    elif category == "Moderate":
        st.warning(f"🟡 MODERATE RISK")
    else:
        st.error(f"🔴 HIGH RISK")

# ── Guard clause ──────────────────────────────────────────────────────────────
if not st.session_state.get("history"):
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);
                border-radius:14px;padding:2rem 2.2rem;color:white;margin-bottom:2rem;">
      <h2 style="color:white;margin:0;">📊 Risk Assessment Results</h2>
      <p style="color:rgba(255,255,255,0.85);margin:0.3rem 0 0;">No assessment found yet.</p>
    </div>""", unsafe_allow_html=True)
    st.warning("Please complete the health assessment form first.")
    if st.button("📋 Go to Assessment", type="primary"):
        st.switch_page("pages/1_Assessment.py")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────
record    = st.session_state["history"][-1]
inputs    = record["inputs"]
diabetes  = record["diabetes"]
cardio    = record["cardio"]
timestamp = record.get("timestamp", "")

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);
            border-radius:14px;padding:2rem 2.2rem;color:white;margin-bottom:2rem;">
  <h2 style="color:white;font-size:1.9rem;font-weight:700;margin:0 0 0.3rem;">📊 Your Risk Assessment Results</h2>
  <p style="color:rgba(255,255,255,0.85);margin:0;">Assessment taken: <strong>{timestamp}</strong></p>
</div>
""", unsafe_allow_html=True)

# ── Section 1: Gauges ─────────────────────────────────────────────────────────
st.subheader("🎯 Risk Score Gauges")
col_d, col_c = st.columns(2, gap="large")

with col_d:
    st.plotly_chart(_gauge("🩸 Diabetes Risk Score", diabetes["hybrid_score"], diabetes["category_color"]),
                    use_container_width=True)
    _badge(diabetes["category"])
    st.caption(f"Hybrid Score: {diabetes['hybrid_score']:.1f} / 100")

with col_c:
    st.plotly_chart(_gauge("❤️ Cardiovascular Risk Score", cardio["hybrid_score"], cardio["category_color"]),
                    use_container_width=True)
    _badge(cardio["category"])
    st.caption(f"Hybrid Score: {cardio['hybrid_score']:.1f} / 100")

st.divider()

# ── Section 2: Score Breakdown ────────────────────────────────────────────────
with st.expander("📈 Score Breakdown Details", expanded=False):
    sb1, sb2 = st.columns(2)
    for col, name, res, icon in [(sb1, "Diabetes", diabetes, "🩸"), (sb2, "Cardiovascular", cardio, "❤️")]:
        with col:
            st.markdown(f"**{icon} {name}**")
            st.markdown(f"- ML Model Probability: **{res['ml_prob']:.1f}%**")
            st.markdown(f"- Clinical Formula Score: **{res['formula_score']:.1f}/100**")
            st.markdown(f"- **Hybrid Score (Final): {res['hybrid_score']:.1f}/100**")
            st.markdown(f"- Category: **{_CAT_ICON[res['category']]} {res['category']}**")
    st.caption("Hybrid Score = 60% ML model probability + 40% clinical formula · Low < 30 · Moderate 30–60 · High > 60")

# ── Section 3: Confidence Disclosure ─────────────────────────────────────────
with st.expander("ℹ️ Model Accuracy & Confidence Disclosure", expanded=False):
    metadata = load_metadata()
    mc1, mc2 = st.columns(2)
    for col, key, name, icon in [
        (mc1, "diabetes", "Diabetes Model", "🩸"),
        (mc2, "cardiovascular", "Cardiovascular Model", "❤️"),
    ]:
        with col:
            m   = metadata.get(key, {})
            acc = f"{float(m['accuracy']):.1%}"    if m.get("accuracy")         else "N/A"
            auc = f"{float(m['roc_auc']):.2f}"     if m.get("roc_auc")          else "N/A"
            n   = f"{m['training_samples']:,}"     if m.get("training_samples") else "N/A"
            cv  = f"{float(m['cv_accuracy']):.1%}" if m.get("cv_accuracy")      else None
            st.markdown(f"**{icon} {name}**")
            st.markdown(f"- Accuracy: **{acc}**")
            st.markdown(f"- ROC-AUC: **{auc}**")
            st.markdown(f"- Training samples: **{n}**")
            if cv:
                st.markdown(f"- CV Accuracy (5-fold): **{cv}**")
    st.warning("⚠️ **Disclaimer:** These scores are for informational and educational purposes only and do not constitute medical advice. Always consult a qualified healthcare professional.")

st.divider()

# ── Section 4: Recommendations ────────────────────────────────────────────────
st.subheader("💡 Personalised Recommendations")

from utils.recommendations import get_recommendations, Recommendation  # noqa: E402

recommendations: list[Recommendation] = get_recommendations(inputs, diabetes, cardio)

_CATEGORY_ORDER = ["Diet", "Exercise", "Checkup", "Lifestyle"]
_CAT_ICONS_MAP  = {"Diet": "🥗", "Exercise": "🏃", "Checkup": "🩺", "Lifestyle": "💤"}
_PRIO_DISPLAY   = {"High": st.error, "Medium": st.warning, "Low": st.info}
_PRIO_BADGE     = {"High": "🔴 HIGH", "Medium": "🟡 MEDIUM", "Low": "🟢 LOW"}

by_category: dict[str, list] = {cat: [] for cat in _CATEGORY_ORDER}
for rec in recommendations:
    if rec.category in by_category:
        by_category[rec.category].append(rec)

rec_cols  = st.columns(2, gap="large")
cat_pairs = [_CATEGORY_ORDER[:2], _CATEGORY_ORDER[2:]]

for col, cats in zip(rec_cols, cat_pairs):
    with col:
        for cat in cats:
            recs = by_category[cat]
            if not recs:
                continue
            st.markdown(f"**{_CAT_ICONS_MAP.get(cat,'')} {cat.upper()}**")
            for rec in recs:
                fn    = _PRIO_DISPLAY.get(rec.priority, st.info)
                badge = _PRIO_BADGE.get(rec.priority, rec.priority)
                fn(f"**[{badge}]** {rec.text}")
            st.write("")

st.divider()

# ── Section 5: Action Buttons ─────────────────────────────────────────────────
btn1, btn2, btn3 = st.columns(3, gap="large")

with btn1:
    if st.button("📋 New Assessment", use_container_width=True, type="secondary"):
        st.switch_page("pages/1_Assessment.py")

with btn2:
    if st.button("📈 View Progress History", use_container_width=True, type="secondary"):
        st.switch_page("pages/3_History.py")

with btn3:
    from utils.pdf_report import generate_pdf  # noqa: E402
    try:
        pdf_bytes = generate_pdf(record)
        fname = f"health_risk_report_{timestamp.replace(':', '').replace(' ', '_')}.pdf"
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes, file_name=fname, mime="application/pdf",
            type="primary", use_container_width=True,
        )
    except Exception as e:
        st.warning(f"PDF generation failed: {e}")
