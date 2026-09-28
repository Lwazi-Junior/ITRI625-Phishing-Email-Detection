# ITRI625 Machine Learning Project

## AI-Based Phishing Email Detection System

This project develops a machine learning/deep learning system for identifying phishing emails.

### Module
ITRI625

### Project Components
- Dataset exploration
- Data preprocessing
- Machine learning baseline
- Deep learning model
- Train/validation/test evaluation
- Early stopping
- Evaluation metrics
- ROC curve
- Precision-Recall curve
- Confusion matrix
- Explainable AI
- FastAPI prediction API
- Desktop application

### Dataset
Phishing Email Dataset

Source:
https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset

### Technologies
- Python
- Jupyter Notebook
- TensorFlow/Keras
- Scikit-learn
- Pandas
- NumPy
- Matplotlib
- FastAPI
- Tkinter
- Explainable AI

## Dataset Setup

This project uses the Kaggle Phishing Email Dataset:

https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset

Download the dataset and place:

`phishing_email.csv`

inside:

`data/raw/`

The raw dataset is excluded from Git version control because of its size.

## FastAPI Prediction Service

The trained 1D CNN model is exposed through a FastAPI service.

### Start the API

From the project root:

```powershell
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### Available endpoints

- `GET /` — service status
- `GET /health` — model health check
- `GET /model-info` — model configuration
- `POST /predict` — phishing email prediction

### Interactive API Documentation

After starting the API, open:

http://127.0.0.1:8000/docs

### Example Prediction Request

```json
{
  "email_text": "URGENT: Verify your account immediately."
}
```

The API returns the predicted class, phishing probability, confidence, risk level and frozen classification threshold.

## Desktop Application

The project includes a Tkinter desktop application that communicates with
the FastAPI prediction service.

### Start the API

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### Start the Desktop Application

Open another terminal:

```powershell
python desktop_app/app.py
```

### Desktop Features

- Raw email text input
- Phishing and legitimate demonstration samples
- FastAPI connectivity monitoring
- AI phishing classification
- Phishing probability
- Legitimate probability
- Prediction confidence
- Risk-level display
- Frozen model threshold display
- Visual phishing-risk meter
- User-friendly API error handling

The desktop interface communicates with the `/predict` API endpoint and
does not load or retrain the machine learning model directly.

## Explainable AI

The system includes local prediction explanations using LIME
(Local Interpretable Model-agnostic Explanations).

### API Endpoint

`POST /explain`

The endpoint returns influential words or phrases and their local
contribution toward the phishing or legitimate class.

### Desktop Integration

After analysing an email, select:

`EXPLAIN PREDICTION`

to open a LIME explanation window.

LIME explanations are local approximations and should not be interpreted
as causal explanations of model behaviour.
