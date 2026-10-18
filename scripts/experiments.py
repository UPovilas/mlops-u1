"""Three explicit hyperparameter settings, each rebuilt and logged to the selected server."""
import json
import os
import subprocess
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[1]
path = root / "params.yaml"
original = path.read_text()
cfg = yaml.safe_load(original)
results = []
try:
    for count, depth in [(10, 2), (50, 4), (100, None)]:
        cfg["train"].update(n_estimators=count, max_depth=depth)
        path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        subprocess.run([str(Path(os.sys.executable).with_name("dvc")), "repro", "--force"], cwd=root, check=True)
        results.append({**json.loads((root / "models/run.json").read_text()), "train": dict(cfg["train"]), "metrics": json.loads((root / "metrics.json").read_text())})
finally:
    path.write_text(original)
(root / "docs/runs.json").write_text(json.dumps(results, indent=2) + "\n")
print("Saved three experiment results to docs/runs.json")
