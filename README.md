# Wine MLOps — U1

Individualus projektas: trijų vyno klasių prognozė pagal 13 cheminių požymių.
Random Forest, CPU; vertinamas atkartojamas eksperimentų srautas.

## Būsena
Pradinis vietinis etapas. Kubernetes, GHCR, Trivy ir galutinis U1 pateikimas dar ruošiami.
Mokymosi gidas: [docs/mokymasis.md](docs/mokymasis.md).

Patikrinta 2026-10-18: prepare → train → evaluate; trys MLflow eksperimentai;
istorinio run'o atkūrimas su jo užrakinta aplinka per **33.084 s**, nekeičiant dabartinių
darbo failų; MLflow saugomo modelio atsisiuntimas ir predict. Kai niekas nepasikeitė,
`dvc repro` praleido visus tris stage'us. Tai vietinio etapo, o ne galutinio U1, patikros.

## Pirmas tavo pratimas
1. MLflow UI atidaryk wine-u1 eksperimentą; palygink n10-d2 ir n100-dNone run'us.
2. Skaityk params.yaml, src/prepare.py, src/train.py, src/evaluate.py ir dvc.yaml.
3. Pakeisk params.yaml n_estimators iš 100 į 30.
4. Terminale nustatyk MLFLOW_TRACKING_URI ir paleisk `uv run dvc repro`.
5. Stebėk: prepare praleidžiamas; train ir evaluate persileidžia; MLflow yra naujas run'as.
6. Grąžink 100 ir dar kartą paleisk dvc repro.

## Aplinka
Reikia Python 3.12, uv, Git. Aplinką užrakina uv.lock.

```bash
uv sync --frozen
```

Duomenys ir modeliai saugomi DVC remote, kuris vietiniam mokymuisi yra gretimas
`../mlops-u1-dvc-store` katalogas. Jis turi išlikti arba būti perkeltas kartu su duomenimis.
Vien Git clone duomenų neatneša: reikia pasiekiamo remote ir `uv run dvc pull`.

## Vietinis MLflow (mokymuisi)
Terminalas 1:
```bash
bash scripts/local_mlflow.sh
```
Metaduomenys: .state/local/mlflow.db. Artefaktai: .state/local/artifacts.
UI: http://127.0.0.1:5001. Šiam vietiniam serveriui autentifikacija neįjungta.

Terminalas 2, projekto kataloge:
```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5001
uv run dvc pull
uv run dvc repro
uv run python scripts/experiments.py
uv run dvc push
```

Prieš mokymą source failai turi būti commit'inti. params.yaml gali keistis: visos
parametrų reikšmės išsaugomos MLflow provenance.json. dvc repro praleidžia
nepasikeitusius stage'us; naujam run'ui pakeisk parametrą arba naudok --force.

## Istorinio run'o atkūrimas
Pasirink run_id iš MLflow arba docs/runs.json:
```bash
uv run python scripts/reproduce.py RUN_ID
```
Scenarijus atsisiunčia run'o provenance.json, išpakuoja to meto Git commit į laikiną
katalogą, per DVC gauna tos versijos duomenis, atkuria parametrus ir vykdo visus tris
stage'us su istoriniame uv.lock užrakinta aplinka. Dabartinis darbo katalogas ir jo parametrai neperrašomi.
Naujas run'as susiejamas `reproduces` žyma; metrikos palyginamos, laikas matuojamas.

## Šaltiniai
- Kurso reikalavimai: https://github.com/VU-MIF-SE/mlops/blob/main/pirma.md
- Wine duomenys: https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_wine.html
- MLflow: https://mlflow.org/docs/latest/ml/tracking/quickstart/
- DVC: https://doc.dvc.org/start

## Likę U1 darbai
- [ ] kind konfigūracija, Namespace, MLflow Deployment + Service + PVC.
- [ ] ≥3 run'ai klasterio MLflow; artefaktai išlieka perkūrus Pod'ą.
- [ ] Dockerfile, GHCR sha-<commit>, vaizdo dydis ir Trivy rezultatas.
- [ ] docs/u1-report.md, patikrintas paleidimas nuo nulio.
- [ ] Viešas GitHub repo, u1-final tag, ZIP eMokymams ir gyvas gynimas.
