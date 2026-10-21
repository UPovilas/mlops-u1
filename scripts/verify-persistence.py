import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import mlflow

root = Path(__file__).resolve().parents[1]
uri = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5002")
if uri != "http://127.0.0.1:5002":
    raise SystemExit("Use the cluster port-forward at http://127.0.0.1:5002.")
mlflow.set_tracking_uri(uri)
client = mlflow.MlflowClient()
run_id = json.loads((root / "docs/runs.json").read_text())[0]["run_id"]
kube = [str(root / ".state/bin/kubectl"), "--kubeconfig", str(root / ".state/kubeconfig"), "-n", "wine-u1"]


def pod(app):
    value = json.loads(subprocess.check_output(kube + ["get", "pods", "-l", f"app={app}", "-o", "json"], text=True))
    return value["items"][0]["metadata"]["uid"]


def snapshot(destination):
    run = client.get_run(run_id)
    provenance = Path(mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="provenance.json", dst_path=str(destination)))
    source = Path(mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="source.tar.gz", dst_path=str(destination)))
    models = client.search_logged_models(experiment_ids=[run.info.experiment_id])
    model = next(model for model in models if model.source_run_id == run_id)
    location = Path(mlflow.artifacts.download_artifacts(artifact_uri=model.model_uri, dst_path=str(destination / "model")))
    model_hashes = {str(path.relative_to(location)): hashlib.sha256(path.read_bytes()).hexdigest() for path in location.rglob("*") if path.is_file()}
    return {"run_id": run_id, "params": dict(run.data.params), "metrics": dict(run.data.metrics), "provenance_sha256": hashlib.sha256(provenance.read_bytes()).hexdigest(), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "model_files": model_hashes}


with tempfile.TemporaryDirectory(prefix="wine-u1-persistence-") as directory:
    work = Path(directory)
    before = snapshot(work / "before")
    pod_ids = {}
    for app in ["mlflow", "postgres"]:
        old = pod(app)
        subprocess.run(kube + ["delete", "pod", "-l", f"app={app}", "--wait=true"], check=True)
        subprocess.run(kube + ["rollout", "status", f"deployment/{app}", "--timeout=180s"], check=True)
        deadline = time.monotonic() + 90
        while True:
            try:
                client.get_run(run_id)
                break
            except Exception:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(2)
        new = pod(app)
        if old == new:
            raise SystemExit(f"{app} Pod UID did not change.")
        pod_ids[app] = {"before": old, "after": new}
    after = snapshot(work / "after")
    if before != after:
        raise SystemExit("Run metadata or artifact hashes changed after Pod recreation.")
    report = {"tracking_uri": uri, "run_id": run_id, "pods": pod_ids, "metadata_and_artifacts_unchanged": True, "artifacts": before}
    (root / "docs/persistence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"run_id": run_id, "metadata_and_artifacts_unchanged": True, "recreated": list(pod_ids)}, indent=2))
