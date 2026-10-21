import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd

root = Path(__file__).resolve().parents[1]
started = time.perf_counter()
uri = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5002")
if uri != "http://127.0.0.1:5002":
    raise SystemExit("Use the Kubernetes MLflow at http://127.0.0.1:5002.")
mlflow.set_tracking_uri(uri)
client = mlflow.MlflowClient()
raw = pd.read_csv(root / "data/raw/wine.csv")
train = pd.read_csv(root / "data/processed/train.csv")
test = pd.read_csv(root / "data/processed/test.csv")
assert raw.shape == (178, 14) and set(raw.target) == {0, 1, 2}
assert not raw.isna().any().any()
assert len(train) + len(test) == len(raw)
assert train.merge(test).empty, "Train and test rows overlap."
runs = json.loads((root / "docs/runs.json").read_text())
assert len({record["run_id"] for record in runs}) >= 3
assert len({(record["train"]["n_estimators"], record["train"]["max_depth"]) for record in runs}) >= 3
for record in runs:
    run = client.get_run(record["run_id"])
    assert run.info.status == "FINISHED"
    assert run.data.tags["data_sha256"] == hashlib.sha256((root / "data/raw/wine.csv").read_bytes()).hexdigest()
    assert run.data.tags["source_sha256"]
    assert set(record["metrics"]).issubset(run.data.metrics)
latest = client.get_run(runs[-1]["run_id"])
models = client.search_logged_models(experiment_ids=[latest.info.experiment_id])
model_record = next(model for model in models if model.source_run_id == latest.info.run_id)
loaded = mlflow.sklearn.load_model(model_record.model_uri)
features = test.drop(columns="target").astype("float64")
assert (loaded.predict(features) == joblib.load(root / "models/model.pkl").predict(features)).all()
dvc = str(Path(sys.executable).with_name("dvc"))
status = json.loads(subprocess.check_output([dvc, "status", "--json"], cwd=root, text=True))
assert not status, status
subprocess.run([dvc, "repro"], cwd=root, check=True)
paths = [root / name for name in ["params.yaml", "dvc.lock", "metrics.json", "models/run.json", "models/model.pkl"]]
before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
subprocess.run([sys.executable, "scripts/reproduce.py", runs[0]["run_id"]], cwd=root, check=True)
after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
assert before == after, "Reproduction modified the current pipeline outputs."
image = json.loads((root / "docs/image.json").read_text())
command = ["docker", "run", "--rm", "--read-only", "--network", "none", "--cap-drop=ALL", "--security-opt", "no-new-privileges"]
predicted = json.loads(subprocess.check_output(command + [image["image"]], text=True))["predictions"]
sample = pd.DataFrame(json.loads((root / "examples/wine.json").read_text()), columns=loaded.feature_names_in_).astype("float64")
assert predicted == loaded.predict(sample).tolist()
assert image["user"] not in {"", "0", "root", "0:0"}
records = json.loads((root / "examples/wine.json").read_text())
with tempfile.TemporaryDirectory(prefix="wine-u1-input-") as directory:
    input_path = Path(directory) / "input.json"
    reordered = [{key: record[key] for key in reversed(list(record))} for record in records]
    input_path.write_text(json.dumps(reordered))
    mounted = command + ["-v", f"{input_path}:/input.json:ro", image["image"], "--input", "/input.json"]
    assert json.loads(subprocess.check_output(mounted, text=True))["predictions"] == predicted
    invalid = [dict(records[0])]
    invalid[0].pop("alcohol")
    input_path.write_text(json.dumps(invalid))
    result = subprocess.run(mounted, capture_output=True, text=True)
    assert result.returncode == 2, result.stderr
report = {
    "tracking_uri": uri,
    "raw_rows": len(raw), "train_rows": len(train), "test_rows": len(test),
    "run_ids": [record["run_id"] for record in runs],
    "three_parameter_settings": True,
    "downloaded_mlflow_model_matches_local_predictions": True,
    "dvc_status_clean": True,
    "reproduction_did_not_change_current_files": True,
    "container_predictions_match": True,
    "container_accepts_reordered_features": True,
    "container_rejects_missing_features": True,
    "container_runs_nonroot_readonly_without_network": True,
    "reproduction_seconds": json.loads((root / "docs/reproduction.json").read_text())["seconds"],
    "verification_seconds": round(time.perf_counter() - started, 3),
}
(root / "docs/verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
