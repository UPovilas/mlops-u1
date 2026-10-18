"""Stage 1: deterministic, stratified train/test split."""
import pandas as pd
from sklearn.model_selection import train_test_split

from common import ROOT, params


def main():
    cfg = params()["split"]
    raw = pd.read_csv(ROOT / "data/raw/wine.csv")
    train, test = train_test_split(raw, stratify=raw["target"], **cfg)
    output = ROOT / "data/processed"
    output.mkdir(parents=True, exist_ok=True)
    train.to_csv(output / "train.csv", index=False)
    test.to_csv(output / "test.csv", index=False)
    print(f"prepare: {len(train)} train / {len(test)} test; seed={cfg['random_state']}")


if __name__ == "__main__":
    main()
