"""Reproduce a historical run without switching branches or overwriting your working files."""
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import mlflow
import yaml

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("run_id")
parser.add_argument("--report", default="docs/reproduction.json")
args = parser.parse_args()
started = time.perf_counter()
uri = os.environ.get("MLFLOW_TRACKING_URI", "")
if not uri.startswith(("http://", "https://")):
    raise SystemExit("Set MLFLOW_TRACKING_URI to the server containing the original run.")
mlflow.set_tracking_uri(uri)
original = mlflow.get_run(args.run_id)
with tempfile.TemporaryDirectory(prefix="wine-u1-reproduce-") as directory:
    work = Path(directory)
    downloaded = mlflow.artifacts.download_artifacts(run_id=args.run_id, artifact_path="provenance.json", dst_path=str(work / "download"))
    provenance = json.loads(Path(downloaded).read_text())
    commit = provenance["git_commit"]
    if provenance.get("source_sha256"):
        downloaded = mlflow.artifacts.download_artifacts(run_id=args.run_id, artifact_path="source.tar.gz", dst_path=str(work / "download"))
        archive = Path(downloaded).read_bytes()
        if hashlib.sha256(archive).hexdigest() != provenance["source_sha256"]:
            raise SystemExit("Source archive hash differs from the original run.")
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            tar.extractall(work, filter="data")
    else:
        archive = subprocess.check_output(["git", "archive", commit], cwd=root)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(work, filter="data")
        (work / "data/raw").mkdir(parents=True, exist_ok=True)
        subprocess.run([str(Path(sys.executable).with_name("dvc")), "get", str(root), "data/raw/wine.csv", "--rev", commit, "--out", str(work / "data/raw/wine.csv")], cwd=root, check=True)
    actual = hashlib.sha256((work / "data/raw/wine.csv").read_bytes()).hexdigest()
    if actual != provenance["data_sha256"]:
        raise SystemExit("Historical data hash does not match the original run.")
    (work / "params.yaml").write_text(yaml.safe_dump(provenance["params"], sort_keys=False))
    env = dict(os.environ, SOURCE_GIT_COMMIT=commit, REPRODUCES_RUN_ID=args.run_id,
               MLFLOW_EXPERIMENT_NAME=mlflow.get_experiment(original.info.experiment_id).name)
    env.pop("VIRTUAL_ENV", None)
    env.pop("UV_PROJECT_ENVIRONMENT", None)
    uv = shutil.which("uv")
    if not uv:
        raise SystemExit("Historical environment restoration requires uv.")
    for stage in ["prepare", "train", "evaluate"]:
        subprocess.run([uv, "run", "--project", str(work), "--frozen", "python", f"src/{stage}.py"], cwd=work, env=env, check=True)
    reproduced = json.loads((work / "metrics.json").read_text())
    new_run = json.loads((work / "models/run.json").read_text())["run_id"]
    for key, value in reproduced.items():
        if abs(value - original.data.metrics[key]) > 1e-12:
            raise SystemExit(f"Metric differs: {key}: {value} vs {original.data.metrics[key]}")
    elapsed = time.perf_counter() - started
    report = {"original_run": args.run_id, "reproduced_run": new_run, "git_commit": commit,
              "source_sha256": provenance.get("source_sha256"), "tracking_uri": uri,
              "data_sha256": actual, "seconds": round(elapsed, 3), "metrics_match": True, "under_120_seconds": elapsed < 120}
    report_path = root / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if elapsed >= 120:
        raise SystemExit("Metrics match, but reproduction exceeded 120 seconds.")
