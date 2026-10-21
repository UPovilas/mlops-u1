# Reikalavimai — v1.1

Problema: pagal 13 cheminių požymių klasifikuoti vyną į vieną iš trijų klasių.
Duomenys: scikit-learn Wine, 178 įrašai. Mokymas CPU, Random Forest.

## Funkciniai reikalavimai

| ID | Reikalavimas | Patikra |
|---|---|---|
| FR-1 | Paruošti train/test, apmokyti ir įvertinti modelį. | Trys DVC stage'ai; metrics.json. |
| FR-2 | Parametrus, metrikas, modelį ir kilmę siųsti į savo klasterio MLflow. | ≥3 run'ai ir parsisiunčiamas modelis. |
| FR-3 | Atkurti pasirinktą istorinį run'ą. | Kodo ir duomenų hash'ai, istorinis uv.lock, metrikų palyginimas. |
| FR-4 | Pateikti paleidžiamą inferencijos konteinerį. | JSON įvestis ir prognozės; netinkama schema atmetama. |

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

Patikros: verification.json, reproduction.json, persistence.json, fresh-start.json,
image.json, scan-summary.json. Naujas įdiegimas gali trukti ilgiau dėl atsisiuntimų;
reprodukcijos KPI neapima pirmo Python paketų parsisiuntimo iš interneto.

## Keitimo istorija

| Versija | Data | Pakeitimas |
|---|---|---|
| 1.0 | 2026-10-18 | Problema ir pradinis reikalavimų rinkinys. |
| 1.1 | 2026-10-19 | Klasterio, saugyklų, reprodukcijos ir konteinerio matavimai. |
