import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
started = time.perf_counter()
with tempfile.TemporaryDirectory(prefix="wine-u1-fresh-") as directory:
    work = Path(directory)
    with zipfile.ZipFile(root / "dist/wine-u1.zip") as package:
        package.extractall(work)
    project = work / "wine-u1"
    shutil.copytree(root / ".git", project / ".git")
    env = dict(os.environ, MLFLOW_TRACKING_URI="http://127.0.0.1:5002", MLFLOW_EXPERIMENT_NAME="wine-u1-fresh-start")
    env.pop("VIRTUAL_ENV", None)
    env.pop("UV_PROJECT_ENVIRONMENT", None)
    def run(command):
        subprocess.run(command, cwd=project, env=env, check=True)
    run(["uv", "sync", "--frozen"])
    run(["bash", "scripts/install-tools.sh"])
    run(["uv", "run", "--frozen", "python", "scripts/bootstrap.py"])
    run(["bash", "scripts/cluster.sh", "up"])
    run(["uv", "run", "--frozen", "python", "scripts/wait-mlflow.py"])
    run(["uv", "run", "--frozen", "dvc", "repro", "--force"])
    run(["uv", "run", "--frozen", "dvc", "push"])
    paths = [project / name for name in ["data/raw/wine.csv", "data/processed/train.csv", "data/processed/test.csv", "models/model.pkl"]]
    hashes = {str(path.relative_to(project)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    for path in paths:
        path.unlink()
    shutil.rmtree(project / ".dvc/cache")
    run(["uv", "run", "--frozen", "dvc", "pull"])
    assert hashes == {str(path.relative_to(project)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    result = json.loads((project / "models/run.json").read_text())
    report = {"clean_project_copy": True, "separate_python_environment": True, "separate_initially_empty_dvc_remote": True, "cluster_setup_idempotent": True, "full_pipeline_passed": True, "cold_cache_restored_from_dvc_remote": True, "run_id": result["run_id"], "tracking_uri": env["MLFLOW_TRACKING_URI"], "seconds": round(time.perf_counter() - started, 3)}
(root / "docs/fresh-start.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
