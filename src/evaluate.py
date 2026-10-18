"""Stage 3: evaluate the held-out test data and attach metrics to the training run."""
import json

import joblib
import mlflow
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from common import ROOT, connect_tracking, write_json


def main():
    connect_tracking()
    model = joblib.load(ROOT / "models/model.pkl")
    test = pd.read_csv(ROOT / "data/processed/test.csv")
    y = test["target"]
    prediction = model.predict(test.drop(columns="target"))
    metrics = {
        "accuracy": float(accuracy_score(y, prediction)),
        "f1_weighted": float(f1_score(y, prediction, average="weighted", zero_division=0)),
        "precision_weighted": float(precision_score(y, prediction, average="weighted", zero_division=0)),
        "recall_weighted": float(recall_score(y, prediction, average="weighted", zero_division=0)),
    }
    write_json(ROOT / "metrics.json", metrics)
    run_id = json.loads((ROOT / "models/run.json").read_text())["run_id"]
    client = mlflow.MlflowClient()
    for key, value in metrics.items():
        client.log_metric(run_id, key, value)
    client.log_artifact(run_id, str(ROOT / "metrics.json"))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
