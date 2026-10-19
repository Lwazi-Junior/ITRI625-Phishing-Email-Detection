import csv
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api.predictor import predictor
from api.security import install_security

# The browser UI: static files only, no model logic.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = PROJECT_ROOT / "web"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
METRICS_DIR = PROJECT_ROOT / "outputs" / "metrics"


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------
app = FastAPI(
    title="PhishGuard AI API",
    description=(
        "FastAPI service for the ITRI625 "
        "AI-Based Phishing Email Detection System."
    ),
    version="1.0.0"
)
explain_slots = install_security(app)
if WEB_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=WEB_DIR, html=True), name="web")
if FIGURES_DIR.is_dir():
    app.mount("/figures", StaticFiles(directory=FIGURES_DIR), name="figures")


# ---------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------
class EmailRequest(BaseModel):
    email_text: str = Field(
        ...,
        min_length=1,
        max_length=200000,
        description=(
            "Raw email text to analyse for phishing."
        )
    )


class PredictionResponse(BaseModel):
    model: str
    predicted_class: int
    prediction: str
    phishing_probability: float
    legitimate_probability: float
    confidence: float
    risk_level: str
    threshold: float


class ExplanationRequest(BaseModel):
    email_text: str = Field(
        ...,
        min_length=1,
        max_length=200000,
        description=(
            "Raw email text to explain."
        )
    )
    num_features: int = Field(
        default=8,
        ge=3,
        le=15
    )
    num_samples: int = Field(
        default=1000,
        ge=100,
        le=3000
    )


class ExplanationFeature(BaseModel):
    feature: str
    weight: float
    absolute_weight: float
    direction: str


class ExplanationResponse(BaseModel):
    model: str
    prediction: str
    predicted_class: int
    phishing_probability: float
    legitimate_probability: float
    confidence: float
    risk_level: str
    threshold: float
    method: str
    target_class: str
    num_features: int
    num_samples: int
    features: list[ExplanationFeature]


@app.get("/", include_in_schema=False)
def root():
    # A visitor at the site root lands on the browser UI when it is present.
    if WEB_DIR.is_dir():
        return RedirectResponse(url="/ui/")
    return {
        "application": "PhishGuard AI",
        "status": "online",
        "message": (
            "AI phishing-email detection service is running."
        )
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": predictor.model_loaded,
        "model": predictor.model_name,
        "decision_threshold": predictor.threshold
    }


@app.get("/model-info")
def model_info():
    return predictor.model_info()


@app.get("/metrics")
def metrics():
    """
    Return the saved final test results, computed once in the notebook.

    Inputs: none.
    Output: the final evaluation metadata and the CNN against baseline table.
    Raises: 503 naming the missing file if the notebook outputs are absent.
    """
    metadata_path = METRICS_DIR / "final_evaluation_metadata.json"
    table_path = METRICS_DIR / "final_test_metrics.csv"
    for path in (metadata_path, table_path):
        if not path.exists():
            raise HTTPException(
                status_code=503,
                detail=f"Metrics file missing: outputs/metrics/{path.name}."
            )
    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    with table_path.open("r", encoding="utf-8", newline="") as handle:
        comparison = [
            {
                "metric": row["Metric"],
                "logistic_regression": float(row["Logistic Regression"]),
                "cnn": float(row["1D CNN"])
            }
            for row in csv.DictReader(handle)
        ]
    return {"final_test": metadata, "comparison": comparison}


@app.post("/predict", response_model=PredictionResponse)
def predict_email(request: EmailRequest):
    try:
        return predictor.predict(request.email_text)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Prediction failed."
        ) from exc


@app.post(
    "/explain",
    response_model=ExplanationResponse
)
def explain_email(request: ExplanationRequest):
    # LIME scores hundreds of variations of the email, so only a few
    # explanations may run at once; the rest are told to retry.
    if not explain_slots.acquire(blocking=False):
        raise HTTPException(
            status_code=503,
            detail=(
                "The server is already running the maximum number of "
                "explanations. Try again in a few seconds."
            )
        )
    try:
        return predictor.explain(
            email_text=request.email_text,
            num_features=request.num_features,
            num_samples=request.num_samples
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error
    except Exception as error:
        # The cause stays in the server log; the client gets no internals.
        raise HTTPException(
            status_code=500,
            detail="Explanation failed."
        ) from error
    finally:
        explain_slots.release()
