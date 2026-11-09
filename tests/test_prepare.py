"""prepare.py splits data/raw/wine.csv; runs in a temp dir so the repo is not touched."""
import pandas as pd

import prepare
from common import params


def test_split(tmp_path, monkeypatch, raw):
    (tmp_path / "data/raw").mkdir(parents=True)
    raw.to_csv(tmp_path / "data/raw/wine.csv", index=False)
    monkeypatch.setattr(prepare, "ROOT", tmp_path)
    prepare.main()

    train = pd.read_csv(tmp_path / "data/processed/train.csv")
    test = pd.read_csv(tmp_path / "data/processed/test.csv")
    test_size = params()["split"]["test_size"]

    assert len(train) + len(test) == len(raw)
    assert len(test) == round(len(raw) * test_size)