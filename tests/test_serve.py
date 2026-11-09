"""API tests without an MLflow server: load_model is replaced with a small local model."""
import importlib
import json
import sys

import mlflow.sklearn
import pytest
from fastapi.testclient import TestClient
from sklearn.ensemble import RandomForestClassifier

from common import ROOT


@pytest.fixture
def client(monkeypatch, raw):
    model = RandomForestClassifier(n_estimators=5, random_state=0).fit(raw.drop(columns="target"), raw["target"])
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://mlflow.test")
    monkeypatch.setattr(mlflow.sklearn, "load_model", lambda uri: model)
    sys.modules.pop("serve", None)
    serve = importlib.import_module("serve")
    return TestClient(serve.app)


@pytest.fixture
def example():
    return json.loads((ROOT / "examples/wine.json").read_text())


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_predict_ok(client, example):
    response = client.post("/predict", json=example)
    assert response.status_code == 200
    assert len(response.json()["predictions"]) == len(example)

def test_predict_missing_feature(client, example):
    del example[0]["alcohol"]
    response = client.post("/predict", json=example)
    assert response.status_code == 422
