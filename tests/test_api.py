"""
test_api.py
Endpoint tests against the saved model: responses, validation and errors.
Author: Colile Sibanda
"""

import json
from pathlib import Path

from tests.conftest import LEGITIMATE_TEXT, PHISHING_TEXT

CONFIG = json.loads(
    (Path(__file__).resolve().parents[1] / "models" / "deep_learning" / "decision_config.json")
    .read_text(encoding="utf-8")
)


def test_health_reports_loaded_model_and_frozen_threshold(client):
    body = client.get("/health").json()
    assert body["model_loaded"] is True
    assert body["decision_threshold"] == CONFIG["selected_threshold"]


def test_predict_flags_obvious_phishing(client):
    body = client.post("/predict", json={"email_text": PHISHING_TEXT}).json()
    assert body["prediction"] == "Phishing"
    assert body["predicted_class"] == 1


def test_predict_passes_ordinary_meeting_email(client):
    body = client.post("/predict", json={"email_text": LEGITIMATE_TEXT}).json()
    assert body["prediction"] == "Legitimate"
    assert body["predicted_class"] == 0


def test_probabilities_are_complementary_and_in_range(client):
    body = client.post("/predict", json={"email_text": PHISHING_TEXT}).json()
    assert 0.0 <= body["phishing_probability"] <= 1.0
    assert abs(body["phishing_probability"] + body["legitimate_probability"] - 1.0) < 1e-6


def test_class_follows_the_frozen_threshold(client):
    for text in (PHISHING_TEXT, LEGITIMATE_TEXT):
        body = client.post("/predict", json={"email_text": text}).json()
        expected = int(body["phishing_probability"] >= body["threshold"])
        assert body["predicted_class"] == expected


def test_empty_text_is_rejected_naming_the_field(client):
    response = client.post("/predict", json={"email_text": ""})
    assert response.status_code == 422
    assert "email_text" in json.dumps(response.json()["detail"])


def test_oversized_text_is_rejected(client):
    response = client.post("/predict", json={"email_text": "a" * 200_001})
    assert response.status_code == 422


def test_explain_returns_weighted_words_from_the_email(client):
    response = client.post(
        "/explain",
        json={"email_text": PHISHING_TEXT, "num_features": 5, "num_samples": 200},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["method"] == "LIME"
    assert 0 < len(body["features"]) <= 5
    for feature in body["features"]:
        assert feature["feature"] in PHISHING_TEXT
        assert feature["absolute_weight"] == abs(feature["weight"])


def test_explain_rejects_out_of_range_settings(client):
    response = client.post(
        "/explain", json={"email_text": PHISHING_TEXT, "num_samples": 50_000}
    )
    assert response.status_code == 422


def test_metrics_serves_the_saved_test_results(client):
    body = client.get("/metrics").json()
    assert body["final_test"]["test_set_used_for_tuning"] is False
    assert {row["metric"] for row in body["comparison"]} >= {"Accuracy", "F1-score", "ROC-AUC"}


def test_browser_ui_and_figures_are_served(client):
    assert client.get("/ui/").status_code == 200
    assert client.get("/ui/about.html").status_code == 200
    assert client.get("/figures/final_test_roc_curve.png").status_code == 200
