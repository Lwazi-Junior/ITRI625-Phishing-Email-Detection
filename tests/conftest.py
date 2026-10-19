"""
conftest.py
Shared fixtures: one API client for the whole run, so the saved model is
loaded once.
Author: Colile Sibanda
"""

import os

import pytest

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

PHISHING_TEXT = (
    "URGENT: Your account has been locked. Verify your password "
    "immediately by clicking this link."
)
LEGITIMATE_TEXT = (
    "Hi team, please remember that our project meeting is scheduled for "
    "tomorrow at 10:00. The agenda is attached. Regards, Michael."
)


@pytest.fixture(scope="session")
def client():
    """
    A TestClient for the real app with the saved model loaded.

    Inputs: none.
    Output: fastapi.testclient.TestClient.
    """
    from fastapi.testclient import TestClient

    from api.main import app

    return TestClient(app)
