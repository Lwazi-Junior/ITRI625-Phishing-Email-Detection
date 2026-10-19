# Dockerfile
# Purpose: one container that serves the PhishGuard API and browser UI.
# Author: Colile Sibanda
#
# Build context is the repository root. Only the served model, its threshold
# file, the saved test results and figures, the API and the UI are copied in;
# data and notebooks never enter the image.

FROM python:3.11-slim

RUN useradd --create-home --uid 1000 user
WORKDIR /app

COPY deploy/requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt

COPY --chown=user api api
COPY --chown=user web web
COPY --chown=user models/deep_learning models/deep_learning
COPY --chown=user outputs/metrics outputs/metrics
COPY --chown=user outputs/figures outputs/figures

USER user
# Small CPU host: keep TensorFlow to a few threads and quiet start-up logs.
ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    TF_NUM_INTRAOP_THREADS=1 \
    TF_NUM_INTEROP_THREADS=1 \
    PORT=10000
EXPOSE 10000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
