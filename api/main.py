from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from api.predictor import predictor


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


@app.get("/")
def root():
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
        raise HTTPException(
            status_code=500,
            detail=(
                "Explanation failed: "
                f"{str(error)}"
            )
        ) from error
