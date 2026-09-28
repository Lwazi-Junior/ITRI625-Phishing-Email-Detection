import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras
from lime.lime_text import LimeTextExplainer


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "deep_learning"
    / "best_phishing_cnn.keras"
)

CONFIG_PATH = (
    PROJECT_ROOT
    / "models"
    / "deep_learning"
    / "decision_config.json"
)


# ---------------------------------------------------------
# Predictor class
# ---------------------------------------------------------
class PhishingPredictor:
    """
    Loads the frozen phishing-detection CNN and exposes
    reusable prediction functionality for the API.

    The model and decision configuration are loaded once
    when the predictor is created, not on every request.
    """

    def __init__(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Saved CNN not found at {MODEL_PATH}"
            )

        if not CONFIG_PATH.exists():
            raise FileNotFoundError(
                f"Decision config not found at {CONFIG_PATH}"
            )

        with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            self.config = json.load(config_file)

        self.model = keras.models.load_model(MODEL_PATH)
        self.model_name = self.config["model"]
        self.threshold = float(self.config["selected_threshold"])
        self.model_loaded = True
        self.explainer = LimeTextExplainer(
            class_names=[
                "Legitimate",
                "Phishing"
            ],
            random_state=42
        )

    def predict(self, email_text: str) -> dict:
        """
        Score one raw email and apply the frozen threshold.
        """
        text = str(email_text)

        phishing_probability = float(
            self.model.predict(
                tf.constant([text], dtype=tf.string),
                verbose=0
            )[0][0]
        )

        legitimate_probability = 1.0 - phishing_probability
        predicted_class = int(
            phishing_probability >= self.threshold
        )

        if predicted_class == 1:
            prediction = "Phishing"
            confidence = phishing_probability
        else:
            prediction = "Legitimate"
            confidence = legitimate_probability

        return {
            "model": self.model_name,
            "predicted_class": predicted_class,
            "prediction": prediction,
            "phishing_probability": phishing_probability,
            "legitimate_probability": legitimate_probability,
            "confidence": confidence,
            "risk_level": self._risk_level(phishing_probability),
            "threshold": self.threshold
        }

    def _risk_level(self, phishing_probability: float) -> str:
        if phishing_probability >= 0.90:
            return "Critical"
        if phishing_probability >= 0.75:
            return "High"
        if phishing_probability >= self.threshold:
            return "Medium"
        if phishing_probability >= 0.25:
            return "Low"
        return "Minimal"

    def _lime_predict_proba(self, texts):
        """
        Probability function used internally by LIME.

        LIME requires a two-column probability matrix:
        column 0 -> Legitimate probability
        column 1 -> Phishing probability
        """
        text_list = [
            str(text)
            for text in texts
        ]
        model_input = tf.constant(
            text_list,
            dtype=tf.string
        )
        phishing_probabilities = (
            self.model.predict(
                model_input,
                verbose=0
            )
            .reshape(-1)
        )
        legitimate_probabilities = (
            1.0 - phishing_probabilities
        )
        return np.column_stack([
            legitimate_probabilities,
            phishing_probabilities
        ])

    def explain(
        self,
        email_text: str,
        num_features: int = 8,
        num_samples: int = 1000
    ) -> dict:
        """
        Generate a local LIME explanation for the
        phishing-class probability.
        """
        if not isinstance(email_text, str):
            raise TypeError(
                "email_text must be a string."
            )

        cleaned_text = email_text.strip()
        if not cleaned_text:
            raise ValueError(
                "Email text cannot be empty."
            )

        prediction_result = self.predict(cleaned_text)
        explanation = (
            self.explainer.explain_instance(
                cleaned_text,
                self._lime_predict_proba,
                labels=[1],
                num_features=num_features,
                num_samples=num_samples
            )
        )

        features = []
        for feature, weight in explanation.as_list(label=1):
            weight = float(weight)
            if weight > 0:
                direction = "Supports phishing"
            elif weight < 0:
                direction = "Supports legitimate"
            else:
                direction = "Neutral"
            features.append({
                "feature": str(feature),
                "weight": weight,
                "absolute_weight": abs(weight),
                "direction": direction
            })

        return {
            "model": prediction_result["model"],
            "prediction": prediction_result["prediction"],
            "predicted_class": prediction_result["predicted_class"],
            "phishing_probability": prediction_result[
                "phishing_probability"
            ],
            "legitimate_probability": prediction_result[
                "legitimate_probability"
            ],
            "confidence": prediction_result["confidence"],
            "risk_level": prediction_result["risk_level"],
            "threshold": prediction_result["threshold"],
            "method": "LIME",
            "target_class": "Phishing",
            "num_features": int(num_features),
            "num_samples": int(num_samples),
            "features": features
        }

    def model_info(self) -> dict:
        return {
            "model": self.model_name,
            "architecture": "1D CNN",
            "layers": [
                layer.name for layer in self.model.layers
            ],
            "classes": {
                "0": "Legitimate",
                "1": "Phishing"
            },
            "decision_threshold": self.threshold,
            "threshold_source": self.config.get(
                "threshold_selection_dataset",
                "validation"
            ),
            "threshold_selection_metric": self.config.get(
                "threshold_selection_metric",
                "F1-score"
            ),
            "input": "raw email text",
            "output": "phishing probability"
        }


predictor = PhishingPredictor()
