"""Stage 4: register the evaluated model and move @champion only if it is at least as good."""
import json

import mlflow

from common import ROOT, connect_tracking

MODEL_NAME = "wine-classifier"
ALIAS = "champion"
METRIC = "accuracy"


def main():
    connect_tracking()
    client = mlflow.MlflowClient()
    run_id = json.loads((ROOT / "models/run.json").read_text())["run_id"]
    new_score = json.loads((ROOT / "metrics.json").read_text())[METRIC]

    # TODO(tu): užregistruok šio run'o modelį vardu MODEL_NAME -> su model uri, kuriame yra run_id ir relative_path="model" — užuomina: client.create_registered_model(...), client.create_model_version(...)
    version = mlflow.register_model(f"runs:/{run_id}/model", MODEL_NAME)

    try:
        champion = client.get_model_version_by_alias(MODEL_NAME, ALIAS)
        champion_score = client.get_run(champion.run_id).data.metrics[METRIC]
    except mlflow.exceptions.MlflowException:
        champion_score = None  # dar nėra champion

    # TODO(tu): taisyklė (b) — kada kviesti client.set_registered_model_alias(MODEL_NAME, ALIAS, version.version)?
    if champion_score is None or new_score >= champion_score:
        client.set_registered_model_alias(MODEL_NAME, ALIAS, version.version)

    print(f"register: {MODEL_NAME} v{version.version} {METRIC}={new_score} champion_before={champion_score}")


if __name__ == "__main__":
    main()
