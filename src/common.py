"""Small shared helpers. Paths are relative to this project, never the shell cwd."""
import hashlib
import gzip
import io
import json
import os
import subprocess
import tarfile
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
    if os.environ.get("SOURCE_GIT_COMMIT"):
        return os.environ["SOURCE_GIT_COMMIT"]
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return "uncommitted"


def source_snapshot():
    files = [ROOT / name for name in ["params.yaml", "pyproject.toml", "uv.lock", "dvc.yaml", ".python-version", "data/raw/wine.csv", "data/raw/wine.csv.dvc"]]
    for directory in ["src", "scripts", "docker", "k8s", "examples"]:
        files.extend(path for path in (ROOT / directory).rglob("*") if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts and path.suffix != ".pyc" and path.name != ".DS_Store" and not path.name.startswith("._"))
    content = io.BytesIO()
    with gzip.GzipFile(fileobj=content, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for path in sorted(files):
                info = archive.gettarinfo(str(path), arcname=path.relative_to(ROOT).as_posix())
                info.mtime = info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mode = 0o644
                with path.open("rb") as stream:
                    archive.addfile(info, stream)
    data = content.getvalue()
    status = subprocess.run(["git", "status", "--porcelain", "--", "src", "scripts", "docker", "k8s", "examples", ".python-version", "params.yaml", "pyproject.toml", "uv.lock", "dvc.yaml", "data/raw/wine.csv.dvc"], cwd=ROOT, capture_output=True, text=True)
    dirty = status.returncode != 0 or bool(status.stdout.strip())
    return data, hashlib.sha256(data).hexdigest(), dirty
