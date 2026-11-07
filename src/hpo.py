"""Hyperparameter search: one parent MLflow run with one nested child run per Optuna trial."""
import os

import mlflow
import optuna
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from common import ROOT, connect_tracking, params, source_commit, write_json


def main():
    connect_tracking()
    cfg = params()
    hpo = cfg["hpo"]
    mlflow.set_experiment(os.environ.get("MLFLOW_EXPERIMENT_NAME", "wine-u1"))
    mlflow.enable_system_metrics_logging()
    mlflow.set_system_metrics_sampling_interval(1)
    train = pd.read_csv(ROOT / "data/processed/train.csv")
    x, y = train.drop(columns="target").astype("float64"), train["target"]
    seed = cfg["train"]["random_state"]

    def objective(trial):
        n_estimators = trial.suggest_int("n_estimators", hpo["n_estimators"]["min"], hpo["n_estimators"]["max"], step=hpo["n_estimators"]["step"])
        max_depth = trial.suggest_int("max_depth", hpo["max_depth"]["min"], hpo["max_depth"]["max"], step=hpo["max_depth"]["step"])
        with mlflow.start_run(run_name=f"trial-{trial.number}", nested=True):
            model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=seed, n_jobs=1, oob_score=True)
            model.fit(x, y)
            mlflow.log_params({"n_estimators": n_estimators, "max_depth": max_depth})
            mlflow.log_metric("oob_score", model.oob_score_)
            return model.oob_score_

    with mlflow.start_run(run_name="hpo"):
        mlflow.set_tags({"git_commit": source_commit(), "seed.train": str(seed)})
        sampler = optuna.samplers.TPESampler(seed=seed)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        study.optimize(objective, n_trials=hpo["n_trials"])
        mlflow.log_params(study.best_params)
        mlflow.log_metric("best_oob_score", study.best_value)
        write_json(ROOT / "models/best_params.json", study.best_params)
        print(f"hpo: best={study.best_value:.4f} params={study.best_params}")


if __name__ == "__main__":
    main()
