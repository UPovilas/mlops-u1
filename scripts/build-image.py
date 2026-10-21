import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
from common import source_commit, source_snapshot

_, source_hash, dirty = source_snapshot()
commit = source_commit()
tag = f"worktree-{source_hash[:12]}" if dirty or commit == "uncommitted" else f"sha-{commit[:12]}"
image = f"wine-u1-inference:{tag}"
subprocess.run(["docker", "build", "-f", "docker/Dockerfile", "--build-arg", f"GIT_COMMIT={commit}", "--build-arg", f"SOURCE_SHA256={source_hash}", "-t", image, "."], cwd=root, check=True)
inspection = json.loads(subprocess.check_output(["docker", "image", "inspect", image], text=True))[0]
result = subprocess.check_output(["docker", "run", "--rm", "--read-only", "--network", "none", "--cap-drop=ALL", "--security-opt", "no-new-privileges", image], text=True)
report = {
    "image": image,
    "image_id": inspection["Id"],
    "architecture": inspection["Architecture"],
    "size_bytes": inspection["Size"],
    "user": inspection["Config"]["User"],
    "git_commit": commit,
    "git_dirty": dirty,
    "source_sha256": source_hash,
    "model_sha256": hashlib.sha256((root / "models/model.pkl").read_bytes()).hexdigest(),
    "predictions": json.loads(result)["predictions"],
}
(root / "docs/image.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
