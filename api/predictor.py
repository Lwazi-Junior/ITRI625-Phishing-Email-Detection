from pathlib import Path
import json

import tensorflow as tf
from tensorflow import keras


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
