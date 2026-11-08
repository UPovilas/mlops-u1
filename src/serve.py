"""Inference API: loads the @champion model from the MLflow registry once at startup."""
import os

import mlflow
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException

from common import connect_tracking

connect_tracking()

# TODO(tu): iš kurio env kintamojo imti modelio adresą? Numatyta reikšmė — champion URI iš Z-04
MODEL_URI = os.environ.get("MODEL_URI", "models:/wine-classifier@champion")

# TODO(tu): pakrauk modelį (vieną kartą, čia, modulio lygyje). Jei MLflow nepasiekiamas — tegul nulūžta (variantas a)
model = mlflow.sklearn.load_model(MODEL_URI)

COLUMNS = list(model.feature_names_in_)
app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok", "model_uri": MODEL_URI}


@app.post("/predict")
def predict(records: list[dict]):
    if not records or any(set(record) != set(COLUMNS) for record in records):
        raise HTTPException(422, "Each record must contain exactly the 13 model features.")
    try:
        features = pd.DataFrame(records, columns=COLUMNS).astype("float64")
    except (TypeError, ValueError):
        raise HTTPException(422, "Feature values must be numeric.")
    if not np.isfinite(features.to_numpy()).all():
        raise HTTPException(422, "Feature values must be finite and not missing.")
    # TODO(tu): grąžink {"predictions": [...]} — kaip predict.py paskutinėje eilutėje
    return {"predictions": model.predict(features).tolist()}
