# Reikalavimai — v1.1

## Problema
Pagal 13 cheminės analizės požymių klasifikuoti vyną į vieną iš trijų klasių.
Duomenys: scikit-learn Wine, 178 įrašai; pirminis šaltinis UCI Wine.
https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_wine.html

## Funkciniai reikalavimai
| ID | Reikalavimas | Patikra |
|---|---|---|
| FR-1 | Paruošti stratifikuotą train/test padalijimą, apmokyti ir įvertinti modelį. | Trys DVC stage'ai; metrics.json. |
| FR-2 | MLflow saugoti parametrus, metrikas, modelį, duomenų hash ir Git commit. | Run'o UI ir provenance.json. |
| FR-3 | Atkurti pasirinktą istorinį run'ą su to meto kodu, duomenimis ir parametrais. | scripts/reproduce.py RUN_ID. |
| FR-4 | MLflow paleisti savo lokaliame Kubernetes klasteryje. | Run'as matomas per port-forward; artefaktą galima atsisiųsti. |

## Nefunkciniai reikalavimai ir KPI
| ID | Reikalavimas | KPI | Matavimas |
|---|---|---|---|
| NFR-1 | Istorinio run'o reprodukcija. | <120 s esant paruoštai aplinkai ir pasiekiamam MLflow/DVC remote. | docs/reproduction.json. |
| NFR-2 | Deterministinė reprodukcija. | Visų keturių vertinimo metrikų skirtumas ≤1e-12 toje pačioje užrakintoje aplinkoje. | Reprodukcijos scenarijaus palyginimas. |
| NFR-3 | Trumpas mokymas CPU. | Vieno modelio fit <30 s, GPU nereikalingas. | MLflow train_seconds. |
| NFR-4 | MLflow duomenų išlikimas. | Po MLflow Pod'o perkūrimo tas pats run_id ir tas pats atsisiųsto artefakto SHA256. | Pod'o perkūrimo patikra. |
| NFR-5 | Atsekamumas. | 100% pateikiamų run'ų turi git_commit, data_sha256 ir parametrus. | MLflow UI / API. |
| NFR-6 | Aplinkos atkartojamumas. | Python 3.12; visos Python priklausomybės užrakintos uv.lock. | uv sync --frozen. |

Tai tikslai ir patikros, o ne teiginys, kad visi matavimai jau atlikti.

## Pirmo vietinio etapo matavimai (2026-10-18)
- Trys pateikiami run'ai: docs/runs.json; visi užbaigti ir turi Git/data žymas.
- Istorinio run'o atkūrimas su jo uv.lock: 33.084 s; visos keturios metrikos sutapo.
- Atkūrimas nepakeitė dabartinių params.yaml, dvc.lock, metrics.json ar models/run.json.
- MLflow modelio atsisiuntimas ir predict patikrinti; rezultatas sutapo su run'o accuracy.
- Kubernetes išlikimo KPI dar neišmatuotas. Vietinis MLflow nepakeičia U1-R4.

## Keitimo istorija
| Versija | Data | Pakeitimas |
|---|---|---|
| 1.0 | 2026-10-18 | Problema, FR, pradinis reikalavimų rinkinys. |
| 1.1 | 2026-10-18 | Užfiksuoti vietinio pipeline'o, atsekamumo ir reprodukcijos matavimai; atskirtos neatliktos patikros. |
