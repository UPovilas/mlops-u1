import collections
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
image = json.loads((root / "docs/image.json").read_text())
subprocess.run(["trivy", "image", "--cache-dir", str(root / ".state/trivy"), "--timeout", "10m", "--scanners", "vuln", "--format", "json", "--output", str(root / "docs/trivy.json"), image["image"]], check=True)
scan = json.loads((root / "docs/trivy.json").read_text())
if scan["Metadata"]["ImageID"] != image["image_id"]:
    raise SystemExit("Scan image ID differs from the built image.")
counts = collections.Counter(vuln["Severity"] for result in scan.get("Results", []) for vuln in result.get("Vulnerabilities", []))
summary = {"image": image["image"], "image_id": image["image_id"], "created_at": scan.get("CreatedAt"), "severity_counts": dict(counts), "critical_gate_passed": counts["CRITICAL"] == 0}
(root / "docs/scan-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
if not summary["critical_gate_passed"]:
    raise SystemExit("CRITICAL findings must be resolved before publication.")
