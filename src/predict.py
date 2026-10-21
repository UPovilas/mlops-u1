import argparse
import json
import os

import joblib
import numpy as np
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="/app/examples/wine.json")
parser.add_argument("--model", default=os.environ.get("MODEL_PATH", "/app/models/model.pkl"))
args = parser.parse_args()
model = joblib.load(args.model)
with open(args.input) as stream:
    records = json.load(stream)
if not isinstance(records, list) or not records:
    parser.error("Input must be a nonempty JSON array of feature objects.")
columns = list(model.feature_names_in_)
if any(not isinstance(record, dict) or set(record) != set(columns) for record in records):
    parser.error("Each record must contain exactly the 13 model features.")
try:
    features = pd.DataFrame(records, columns=columns).astype("float64")
except (TypeError, ValueError):
    parser.error("Feature values must be numeric.")
if not np.isfinite(features.to_numpy()).all():
    parser.error("Feature values must be finite and not missing.")
print(json.dumps({"predictions": model.predict(features).tolist()}))
