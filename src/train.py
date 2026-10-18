"""Stage 2: train, save the model, and log provenance and artifacts to MLflow."""
import os
import time

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier

from common import ROOT, connect_tracking, params, sha256, source_commit, write_json


def main():
    uri = connect_tracking()
    cfg = params()
    commit = source_commit()
    experiment = os.environ.get("MLFLOW_EXPERIMENT_NAME", "wine-u1")
    mlflow.set_experiment(experiment)
    train = pd.read_csv(ROOT / "data/processed/train.csv")
    x, y = train.drop(columns="target"), train["target"]
    provenance = {
        "git_commit": commit,
        "params": cfg,
        "data_sha256": sha256(ROOT / "data/raw/wine.csv"),
        "sklearn_version": sklearn.__version__,
    }
    with mlflow.start_run(run_name=f"rf-n{cfg['train']['n_estimators']}-d{cfg['train']['max_depth']}") as run:
        mlflow.log_params({f"{section}.{key}": value for section, values in cfg.items() for key, value in values.items()})
        mlflow.set_tags({"git_commit": commit, "data_sha256": provenance["data_sha256"], "model_family": "RandomForestClassifier"})
        if os.environ.get("REPRODUCES_RUN_ID"):
            mlflow.set_tag("reproduces", os.environ["REPRODUCES_RUN_ID"])
        mlflow.log_input(mlflow.data.from_pandas(train, targets="target", name="wine-train"), context="training")
        start = time.perf_counter()
        model = RandomForestClassifier(**cfg["train"], n_jobs=1)
        model.fit(x, y)
        mlflow.log_metric("train_seconds", time.perf_counter() - start)
        (ROOT / "models").mkdir(exist_ok=True)
        joblib.dump(model, ROOT / "models/model.pkl")
        mlflow.sklearn.log_model(
            model, name="model", input_example=x.head(3),
            pip_requirements=[f"scikit-learn=={sklearn.__version__}", f"pandas=={pd.__version__}", f"joblib=={joblib.__version__}"],
        )
        mlflow.log_dict(provenance, "provenance.json")
        write_json(ROOT / "models/run.json", {"run_id": run.info.run_id, "experiment": experiment, "git_commit": commit})
        print(f"train: run_id={run.info.run_id}; tracking={uri}")


if __name__ == "__main__":
    main()
