"""Create the source CSV once; DVC then versions its exact bytes."""
from pathlib import Path

from sklearn.datasets import load_wine

root = Path(__file__).resolve().parents[1]
path = root / "data/raw/wine.csv"
if path.exists():
    raise SystemExit(f"Already exists: {path}. Use DVC to restore existing data.")
path.parent.mkdir(parents=True, exist_ok=True)
load_wine(as_frame=True).frame.to_csv(path, index=False)
print(f"Exported Wine dataset to {path}")
