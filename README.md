# Health Risk Assessment Dashboard

A **Streamlit** web application that lets users input lifestyle and basic health data and receive personalised risk scores for **diabetes** and **cardiovascular disease**, complete with recommendations and a downloadable PDF report.

Live demo: deployed on [Streamlit Community Cloud](https://healthguard-hcrldeawmugnxomhqdywch.streamlit.app/)

---

## Features

- 📋 **Health Assessment Form** — collects age, BMI, blood pressure, glucose, cholesterol, smoking, activity level, and more
- 📊 **Risk Gauges** — Plotly gauge charts showing Diabetes and CVD risk on a 0–100 scale (Low / Moderate / High)
- 🔬 **Hybrid Scoring** — combines an ML model prediction with a clinical formula (ADA / Framingham-style) for transparency
- 💡 **Personalised Recommendations** — rule-based engine produces 4–8 actionable items across Diet, Exercise, Checkup, and Lifestyle categories
- 📄 **PDF Report** — downloadable single-page summary generated with `fpdf2`
- 📈 **Session History** — trend chart of risk scores across multiple assessments within the same browser session
- 🔍 **Confidence Disclosure** — expandable panel showing model accuracy, AUC, training dataset size, and a disclaimer

---

## Tech Stack

| Component | Library |
|---|---|
| UI & Hosting | Streamlit |
| ML Models | scikit-learn |
| Charts & Gauges | Plotly |
| PDF Generation | fpdf2 |
| Data Processing | pandas, numpy |
| Model Serialisation | joblib |

---

## Local Setup

### Prerequisites

- Python 3.9 or higher
- `pip`

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/akhiranandan6/health_prediction.git
cd health_prediction

# 2. (Optional) Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501` in your default browser.

---

## Project Structure

```
health_prediction/
├── app.py                          # Streamlit entry point (home page)
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml                 # Theme and server settings
├── pages/
│   ├── 1_Assessment.py             # Health data intake form
│   ├── 2_Results.py                # Risk gauges + recommendations
│   └── 3_History.py                # Session progress tracking
├── models/
│   ├── __init__.py
│   ├── train_models.py             # Offline training script (run once)
│   ├── diabetes_model.pkl          # Trained diabetes pipeline
│   ├── cardio_model.pkl            # Trained cardiovascular pipeline
│   └── model_metadata.json         # Accuracy, AUC, training info
├── utils/
│   ├── __init__.py
│   ├── scoring.py                  # Hybrid scorer (ML + clinical formula)
│   ├── recommendations.py          # Rule-based recommendation engine
│   └── pdf_report.py               # fpdf2 PDF generation
└── data/
    ├── diabetes.csv
    ├── cardio_train.csv
    └── healthcare_synthetic_data.csv
```

---

## Datasets

| File | Source | Rows | Target |
|---|---|---|---|
| `data/diabetes.csv` | [Pima Indians Diabetes Dataset](https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database) — UCI / Kaggle | ~769 | `Outcome` (1 = diabetic) |
| `data/cardio_train.csv` | [Cardiovascular Disease Dataset](https://www.kaggle.com/datasets/sulianova/cardiovascular-disease-dataset) — Kaggle | ~70,000 | `cardio` (1 = CVD present) |
| `data/healthcare_synthetic_data.csv` | [Synthetic Healthcare Dataset](https://www.kaggle.com/datasets/prasad22/healthcare-dataset) — Kaggle | ~10,020 | `Heart_Disease_Risk` |

### Attribution

- **Pima Indians Diabetes Database** — originally from the National Institute of Diabetes and Digestive and Kidney Diseases. Hosted on Kaggle by UCI Machine Learning.
- **Cardiovascular Disease Dataset** — compiled and published on Kaggle by Svetlana Ulianova.
- **Synthetic Healthcare Dataset** — synthetic data published on Kaggle by Prasad; used as supplementary data for the cardiovascular model.

---

## Disclaimer

> The risk scores produced by this application are for **informational and educational purposes only**. They do not constitute medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional regarding your health.
