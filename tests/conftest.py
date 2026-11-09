import sys
from pathlib import Path

import pytest
from sklearn.datasets import load_wine

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def raw():
    """Same 178 rows as data/raw/wine.csv, but available in CI where the DVC remote is not."""
    return load_wine(as_frame=True).frame
