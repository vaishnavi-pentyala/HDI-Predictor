# Human Development Index (HDI) Predictor Web Application

An advanced machine learning portal that calculates and predicts Human Development Index (HDI) tiers (Very High, High, Medium, Low) based on UNDP methodologies. It explains predictions using Local Centroid Differences (Explainable AI), exposes interactive analytics dashboards, logs history in SQLite, and exports predictions as PDF reports.

## Features
- **Machine Learning Pipeline:** Trains multiple classifiers (Random Forest, Gradient Boosting, KNN, Logistic Regression) on standardized country metrics, selects the best model, and outputs performance logs.
- **Explainable AI (XAI):** Renders interactive sub-index gauges, highlights poorest dimensions ("Weakest Link"), and displays comparison matrices showing inputs relative to class medians.
- **Interactive Dashboard:** Embeds dynamic Plotly statistics and static Seaborn confusion/correlation heatmaps.
- **Local History Database:** Stores runs in SQLite, clear logs, or exports them as a CSV.
- **Dark Mode & Light Mode:** Sleek glassmorphism theme that persists via `localStorage`.
- **PDF Generation:** Outputs beautiful, printable PDF calculation certificates.

---

## Folder Structure
```
HDI_Predictor/
│
├── app.py                # Flask Server & API Routing
├── train_model.py        # ML Training Pipeline
├── generate_dataset.py   # Dataset Generator / Downloader
├── requirements.txt      # Python Dependencies
├── hdi_history.db        # SQLite Local Database (Auto-created)
├── model.pkl             # Trained Classifier & Preprocessing structures
│
├── templates/            # HTML Templates
│   ├── index.html        # Home / Welcome
│   ├── predict.html      # Predictor Portal & History log
│   ├── dashboard.html    # Analytics Plots
│   └── about.html        # Methodology details
│
├── static/
│   ├── css/
│   │   └── styles.css    # Premium CSS Theme Styles
│   ├── js/
│   │   └── main.js       # Client Logic & API calls
│   └── images/           # Pre-rendered Charts (Confusion matrix, heatmaps)
│
├── charts/               # Pre-rendered Charts backup
└── reports/              # Model reports folder
```

---

## Setup & Installation

### Prerequisites
- Python 3.13+ installed.

### Steps
1. Navigate to the project directory:
   ```bash
   cd C:/Users/vaish/.gemini/antigravity/scratch/HDI_Predictor
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Generate the dataset and run the training pipeline:
   ```bash
   python generate_dataset.py
   python train_model.py
   ```
   *This downloads the real dataset (or generates a synthetic equivalent if offline) and saves the trained model as `model.pkl` along with static evaluation charts.*
4. Start the Flask application:
   ```bash
   python app.py
   ```
5. Open your browser and navigate to: `http://127.0.0.1:5000`

---

## Deployment Instructions

### Deploying to Render
1. Create a free account on [Render](https://render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your Git repository containing this code.
4. Set the following configurations:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt && python generate_dataset.py && python train_model.py`
   - **Start Command:** `gunicorn app:app` (Make sure to add `gunicorn` to your requirements.txt for production, or start with `python app.py` for testing).
5. Click **Deploy Web Service**.

### Deploying to Railway
1. Sign up on [Railway.app](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Connect your repository.
4. Railway automatically detects `requirements.txt`.
5. Add a custom start command in Settings (under Deploy if needed):
   ```bash
   python generate_dataset.py && python train_model.py && python app.py
   ```
6. Deploy and copy the public URL.
