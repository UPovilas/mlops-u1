# Reikalavimai — v1.6

Problema: pagal 13 cheminių požymių klasifikuoti vyną į vieną iš trijų klasių.
Duomenys: scikit-learn Wine, 178 įrašai. Mokymas CPU, Random Forest.

## Funkciniai reikalavimai

| ID | Reikalavimas | Patikra |
|---|---|---|
| FR-1 | Paruošti train/test, apmokyti ir įvertinti modelį. | Trys DVC stage'ai; metrics.json. |
| FR-2 | Parametrus, metrikas, modelį ir kilmę siųsti į savo klasterio MLflow. | ≥3 run'ai ir parsisiunčiamas modelis. |
| FR-3 | Atkurti pasirinktą istorinį run'ą. | Kodo ir duomenų hash'ai, istorinis uv.lock, metrikų palyginimas. |
| FR-4 | Pateikti paleidžiamą inferencijos konteinerį. | JSON įvestis ir prognozės; netinkama schema atmetama. |
| FR-5 | Hiperparametrų paieška kaip tėvinis MLflow run'as su ≥5 nested bandymais. | `src/hpo.py`, Optuna, 10 bandymų; OOB tikslas. |
| FR-6 | Įvertintas modelis registruojamas `wine-classifier`; `@champion` perkeliamas tik jei accuracy ≥ dabartinio. | `src/register.py`; versijos v1–v8. |
| FR-7 | Mokymas vyksta K8s Job klasteryje; parametrai per ConfigMap, prisijungimai per Secret (ne Git'e). | `k8s/train-job.yaml`, Job `Complete`. |
| FR-8 | Inferencijos API klasteryje (`/health`, `/predict`) krauna `models:/wine-classifier@champion`. | `k8s/api.yaml`, `src/serve.py`. |
| FR-9 | CI: ruff + pytest + API vaizdo build/push į GHCR. | `.github/workflows/ci.yml`, žalias. |
| FR-10 | CD su kokybės vartu: blogas modelis neregistruojamas ir nediegiamas; rollback per `@champion`. | `.github/workflows/cd.yml`; žalias ir raudonas paleidimai. |

## Nefunkciniai reikalavimai

| ID | KPI | Išmatuota |
|---|---|---|
| NFR-1 | Istorinio run'o atkūrimas <120 s, kai Python paketai yra vietiniame uv cache. | 28.478 s. |
| NFR-2 | Visų keturių atkurtų metrikų skirtumas ≤1e-12. | Visos sutapo. |
| NFR-3 | Vienas Random Forest fit CPU <30 s. | Didžiausia trukmė 0.069 s. |
| NFR-4 | Perkūrus MLflow ir PostgreSQL Pod'us išlieka run'o metaduomenys ir artefaktų SHA256. | PASS. |
| NFR-5 | 100% pateikiamų run'ų turi parametrus, Git bazę, duomenų ir kodo SHA256. | Patikrinti 3 run'ai. |
| NFR-6 | Python 3.12, priklausomybės iš uv.lock, paleidimas atskiroje aplinkoje. | Fresh-start patikra PASS. |
| NFR-7 | Inferencijos vaizdas ≤500 MB, vartotojas ne root. | 411.76 MB; UID 10001:10001. |
| NFR-8 | Publikavimo metu 0 CRITICAL Trivy radinių. | 0; HIGH 44 aptarti security-scan.md. |
| NFR-9 | `/predict` p95 ≤ 50 ms, 10 vienalaikių vartotojų. | p50 9 ms, p95 19 ms, p99 170 ms (Locust per port-forward, 1 Pod'as; `docs/load/predict-u10_stats.csv`). |
| NFR-10 | `/predict` p95 ≤ 50 ms, 40 vienalaikių vartotojų su HPA (1–3 Pod'ai). | p50 4 ms, p95 8 ms, p99 17 ms, 0 klaidų (Locust klasteryje, 3 Pod'ai; `docs/load/predict-u40-in-cluster-3pods.txt`). |
| NFR-11 | Kokybės vartas: test accuracy ≥ 0.85, kitaip CD raudonas. | Žalias: 1.0000; raudonas: 0.6389 (`gate: fail`). |
| NFR-12 | Inferencijos vaizdas ≤500 MB, vartotojas ne root (U2 API). | 476 MB (`docker images`); UID 10001:10001. |

Patikros: verification.json, reproduction.json, persistence.json, fresh-start.json,
image.json, scan-summary.json. Naujas įdiegimas gali trukti ilgiau dėl atsisiuntimų;
reprodukcijos KPI neapima pirmo Python paketų parsisiuntimo iš interneto.

## Keitimo istorija

| Versija | Data | Pakeitimas |
|---|---|---|
| 1.0 | 2026-10-18 | Problema ir pradinis reikalavimų rinkinys. |
| 1.1 | 2026-10-18 | Pirmi vietinio pipeline'o ir reprodukcijos matavimai. |
| 1.1 | 2026-10-21 | Papildyti klasterio, saugyklų ir konteinerio matavimai. |
| 1.2 | 2026-11-07 | U2-R1: seed žymos, sistemos metrikos, OOB kreivė, HPO su nested run'ais (FR-5). |
| 1.3 | 2026-11-07 | U2-R2: registras ir `@champion` taisyklė (FR-6). |
| 1.4 | 2026-11-08 | U2-R3/R4: mokymo Job, ConfigMap/Secret, inferencijos API (FR-7, FR-8). |
| 1.5 | 2026-11-09 | U2-R5/R6: CI, CD su kokybės vartu, rollback (FR-9, FR-10, NFR-11). |
| 1.6 | 2026-11-10 | U2-R4 matavimai ir E3: p95 (NFR-9), HPA su Locust klasteryje (NFR-10), API vaizdo dydis (NFR-12). |
