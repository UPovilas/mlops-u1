FROM python:3.12-slim-trixie@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS base
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

FROM base AS builder
COPY docker/requirements-inference.txt /tmp/requirements.txt
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --no-compile -r /tmp/requirements.txt \
    && /opt/venv/bin/pip uninstall -y pip

FROM base AS runtime
ARG GIT_COMMIT=uncommitted
ARG SOURCE_SHA256
LABEL org.opencontainers.image.revision=$GIT_COMMIT
LABEL org.opencontainers.image.source="https://github.com/UPovilas/mlops-u1"
LABEL lt.vu.wine.source-sha256=$SOURCE_SHA256
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY src/predict.py /app/src/predict.py
COPY models/model.pkl /app/models/model.pkl
COPY examples/wine.json /app/examples/wine.json
RUN /usr/local/bin/python -m pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3.12/ensurepip \
    && useradd --uid 10001 --create-home appuser
USER 10001:10001
ENTRYPOINT ["python", "/app/src/predict.py"]
