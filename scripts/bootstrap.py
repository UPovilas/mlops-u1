import hashlib
import subprocess
import sys
from pathlib import Path

import yaml
from sklearn.datasets import load_wine

root = Path(__file__).resolve().parents[1]
dvc = str(Path(sys.executable).with_name("dvc"))
remote = root.parent / "mlops-u1-dvc-store"
remote.mkdir(exist_ok=True)
subprocess.run([dvc, "remote", "modify", "--local", "local", "url", str(remote)], cwd=root, check=True)
raw = root / "data/raw/wine.csv"
if not raw.exists():
    restored = subprocess.run([dvc, "pull", "data/raw/wine.csv.dvc"], cwd=root, capture_output=True, text=True)
    if restored.returncode:
        raw.parent.mkdir(parents=True, exist_ok=True)
        load_wine(as_frame=True).frame.to_csv(raw, index=False)
expected = yaml.safe_load((root / "data/raw/wine.csv.dvc").read_text())["outs"][0]["md5"]
if hashlib.md5(raw.read_bytes()).hexdigest() != expected:
    raise SystemExit("Wine CSV differs from the versioned DVC pointer.")
subprocess.run([dvc, "push", "data/raw/wine.csv.dvc"], cwd=root, check=True)
print(f"Data verified; local DVC remote: {remote}")
