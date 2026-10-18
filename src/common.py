"""Small shared helpers. Paths are relative to this project, never the shell cwd."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

import mlflow
import yaml

ROOT = Path(__file__).resolve().parents[1]


def params():
    return yaml.safe_load((ROOT / "params.yaml").read_text())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def connect_tracking():
    uri = os.environ.get("MLFLOW_TRACKING_URI", "")
    if not uri.startswith(("http://", "https://")):
        raise RuntimeError("Set MLFLOW_TRACKING_URI to your running MLflow HTTP server.")
    mlflow.set_tracking_uri(uri)
    return uri


def source_commit():
    # Historical reproduction runs an archived, immutable commit in a temporary directory.
    if os.environ.get("SOURCE_GIT_COMMIT"):
        return os.environ["SOURCE_GIT_COMMIT"]
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--", "src", "scripts", "pyproject.toml", "uv.lock", "dvc.yaml"],
        cwd=ROOT, check=True, stdout=subprocess.DEVNULL,
    )
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
