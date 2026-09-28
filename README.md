# PhishGuard AI
## AI-Based Phishing Email Detection System

ITRI625 Machine Learning Project

PhishGuard AI is an end-to-end cybersecurity machine learning system that
classifies email messages as legitimate or phishing.

The project includes:

- Phishing email dataset preparation
- Logistic Regression baseline
- 1D CNN deep learning classifier
- Train/validation/test experimental design
- Early stopping
- Evaluation metrics and visualisations
- Frozen decision threshold
- FastAPI REST API
- Tkinter desktop application
- LIME Explainable AI

## Dataset

The project uses the combined Kaggle Phishing Email Dataset:

https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset

Place `phishing_email.csv` in `data/raw/`. The notebook cleans the file,
removes exact duplicates, and creates a stratified 70/15/15
train/validation/test split saved under `data/processed/`.

The raw and processed CSV files stay on the local machine. They are excluded
from Git because of their size.

Labels used by the project:

- `0` — legitimate
- `1` — phishing

## Project Structure

```text
api/                  FastAPI service and frozen-model predictor
data/raw/             Local raw CSV (not committed)
data/processed/       Local train, validation and test CSV files (not committed)
desktop_app/          Tkinter client
models/baseline/      TF-IDF vectoriser and logistic regression
models/deep_learning/ Frozen 1D CNN and validation decision config
notebooks/            Executed experiment notebook
outputs/figures/      Saved evaluation and LIME figures
outputs/metrics/      Metric tables and final evaluation metadata
```

## Installation

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`environment_freeze.txt` records the package versions used for the experiment.

## Running the API

The API loads the saved 1D CNN. It does not retrain the model.

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Interactive documentation:

http://127.0.0.1:8000/docs

## Running the Desktop App

Start the API first, then open a second terminal:

```powershell
python desktop_app/app.py
```

The desktop application sends email text to the API. It does not load or
retrain the machine learning model.

## API Endpoints

- `GET /` — service status
- `GET /health` — model health check and frozen threshold
- `GET /model-info` — model configuration
- `POST /predict` — phishing classification
- `POST /explain` — local LIME explanation

Example prediction request:

```json
{
  "email_text": "URGENT: Verify your account immediately."
}
```

The prediction response includes the predicted class, phishing probability,
legitimate probability, confidence, risk level and frozen threshold.

## Final Model Performance

The final frozen 1D CNN was evaluated once on the independent test set.

| Metric | Score |
|---|---:|
| Accuracy | 98.99% |
| Precision | 98.66% |
| Recall | 99.42% |
| F1-score | 99.04% |
| ROC-AUC | 99.95% |
| PR-AUC | 99.95% |
| False Positive Rate | 1.48% |
| False Negative Rate | 0.58% |

The final decision threshold is **0.54**, selected using validation F1-score
before the independent test set was evaluated.

On the 12,312-email test set the confusion matrix was 5,798 true negatives,
87 false positives, 37 false negatives and 6,390 true positives. These values
are stored in `outputs/metrics/final_test_metrics.csv` and
`outputs/metrics/final_evaluation_metadata.json`.

The logistic regression baseline was also scored on the same test set for
comparison. The notebook records both results. The test set was not used to
tune the model or the threshold.

## Explainable AI

The system includes local prediction explanations using LIME
(Local Interpretable Model-agnostic Explanations).

`POST /explain` returns influential words or phrases and their local
contribution toward the phishing or legitimate class.

After analysing an email in the desktop application, select
`EXPLAIN PREDICTION` to open a LIME explanation window.

LIME explanations are local approximations and should not be interpreted
as causal explanations of model behaviour.

## GitHub / Version Control

The implementation was committed step by step, from the initial project
structure through dataset preparation, the baseline, CNN training, validation,
the locked test evaluation, FastAPI, the desktop application and LIME.

Repository:

https://github.com/Lwazi-Junior/ITRI625-Phishing-Email-Detection
