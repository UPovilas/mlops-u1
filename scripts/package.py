import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = [root / name for name in ["README.md", ".gitignore", ".python-version", ".dockerignore", "pyproject.toml", "uv.lock", "params.yaml", "dvc.yaml", "dvc.lock", "metrics.json", "data/raw/wine.csv.dvc", "models/run.json", ".dvc/config", ".dvc/.gitignore", ".dvcignore"]]
for directory in ["src", "scripts", "docker", "k8s", "examples", "docs"]:
    paths.extend(path for path in (root / directory).rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc" and path.name != ".DS_Store")
output = root / "dist"
output.mkdir(exist_ok=True)
archive = output / "wine-u1.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
    for path in sorted(set(paths)):
        if path.exists():
            package.write(path, arcname="wine-u1/" + path.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as package:
    names = package.namelist()
    assert not any(any(part in {".git", ".state", ".venv", "__pycache__"} for part in Path(name).parts) for name in names)
report = {"file": str(archive), "size_bytes": archive.stat().st_size, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "files": len(names)}
(output / "package.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
