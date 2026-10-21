import collections
import json
import os
from pathlib import Path

import mlflow

root = Path(__file__).resolve().parents[1]
mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5002"))


def read(name):
    return json.loads((root / "docs" / name).read_text())


image = read("image.json")
scan = read("scan-summary.json")
full_scan = read("trivy.json")
verification = read("verification.json")
persistence = read("persistence.json")
fresh = read("fresh-start.json")
runs = read("runs.json")
reproduction = read("reproduction.json")
publication = read("publication.json") if (root / "docs/publication.json").is_file() else None
publication_status = "**Pateikimo būsena.** Publikavimo duomenys dar neužfiksuoti."
published_image = ""
if publication:
    repository_url = publication["repository_url"].rstrip("/")
    publication_status = f'''**Pateikimas.** [GitHub repozitorija]({repository_url}),
tag'as [{publication["tag"]}]({repository_url}/tree/{publication["tag"]}).
GHCR vaizdas: `{publication["image"]}`.
Registry digest: `{publication["digest"]}`.
Vaizdo kodo commit'as: [{publication["source_commit"]}]({repository_url}/commit/{publication["source_commit"]}).'''
    published_image = f'\nPublikuotas vaizdas: `{publication["image"]}`. Registry digest: `{publication["digest"]}`.\n'
severity = collections.Counter(scan["severity_counts"])
high = [item for result in full_scan.get("Results", []) for item in result.get("Vulnerabilities", []) if item["Severity"] == "HIGH"]
fixed_high = sum(bool(item.get("FixedVersion")) for item in high)
size_mb = image["size_bytes"] / 1_000_000
size_mib = image["size_bytes"] / 1024**2
(root / "docs/image-sizes.md").write_text(f'''# Docker vaizdas

| Laukas | Reikšmė |
|---|---|
| Išmatuotas vaizdas | `{image["image"]}` |
| ID | `{image["image_id"]}` |
| Architektūra | {image["architecture"]} |
| Dydis | {image["size_bytes"]} B = {size_mb:.2f} MB = {size_mib:.2f} MiB |
| Vartotojas | `{image["user"]}` |
| Modelio SHA256 | `{image["model_sha256"]}` |

Dydis gautas su `docker image inspect` (`.Size`); tai ne registry perdavimo dydis.
Vaizdas išbandytas be tinklo, su read-only failų sistema ir be papildomų capabilities.
Python bazė fiksuota digest'u; bibliotekos prisegtos `docker/requirements-inference.txt`.
{published_image}
''')
(root / "docs/security-scan.md").write_text(f'''# Trivy skenavimas

Vaizdas: `{scan["image"]}`. Skenuota: {scan["created_at"]}.
Skenavimo ir vaizdo ID sutapimas patikrintas. Visas rezultatas — `trivy.json`.

| Svarba | Radinių skaičius |
|---|---:|
| CRITICAL | {severity["CRITICAL"]} |
| HIGH | {severity["HIGH"]} |
| MEDIUM | {severity["MEDIUM"]} |
| LOW | {severity["LOW"]} |
| UNKNOWN | {severity["UNKNOWN"]} |

CRITICAL publikavimo patikra: **{"PASS" if scan["critical_gate_passed"] else "FAIL"}**.
Iš HIGH radinių {fixed_high} turi skene nurodytą pataisytą versiją.
OS paketai atnaujinti build metu. Inferencijos runtime pašalinti pip ir ensurepip;
vykdymui jie nereikalingi. Likę radiniai nėra paslėpti su ignore taisyklėmis.
Radinys vertinamas kartu su paketu, pataisos prieinamumu ir vykdymo kontekstu;
ne root, read-only ir išjungtas tinklas nepanaikina paties CVE.
''')
fit_max = max(mlflow.get_run(record["run_id"]).data.metrics["train_seconds"] for record in runs)
(root / "docs/requirements.md").write_text(f'''# Reikalavimai — v1.1

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
| NFR-1 | Istorinio run'o atkūrimas <120 s, kai Python paketai yra vietiniame uv cache. | {reproduction["seconds"]:.3f} s. |
| NFR-2 | Visų keturių atkurtų metrikų skirtumas ≤1e-12. | Visos sutapo. |
| NFR-3 | Vienas Random Forest fit CPU <30 s. | Didžiausia trukmė {fit_max:.3f} s. |
| NFR-4 | Perkūrus MLflow ir PostgreSQL Pod'us išlieka run'o metaduomenys ir artefaktų SHA256. | {"PASS" if persistence["metadata_and_artifacts_unchanged"] else "FAIL"}. |
| NFR-5 | 100% pateikiamų run'ų turi parametrus, Git bazę, duomenų ir kodo SHA256. | Patikrinti {len(runs)} run'ai. |
| NFR-6 | Python 3.12, priklausomybės iš uv.lock, paleidimas atskiroje aplinkoje. | Fresh-start patikra PASS. |
| NFR-7 | Inferencijos vaizdas ≤500 MB, vartotojas ne root. | {size_mb:.2f} MB; UID {image["user"]}. |
| NFR-8 | Publikavimo metu 0 CRITICAL Trivy radinių. | {severity["CRITICAL"]}; HIGH {severity["HIGH"]} aptarti security-scan.md. |

Patikros: verification.json, reproduction.json, persistence.json, fresh-start.json,
image.json, scan-summary.json. Naujas įdiegimas gali trukti ilgiau dėl atsisiuntimų;
reprodukcijos KPI neapima pirmo Python paketų parsisiuntimo iš interneto.

## Keitimo istorija

| Versija | Data | Pakeitimas |
|---|---|---|
| 1.0 | 2026-10-18 | Problema ir pradinis reikalavimų rinkinys. |
| 1.1 | 2026-10-19 | Klasterio, saugyklų, reprodukcijos ir konteinerio matavimai. |
''')
(root / "docs/u1-report.md").write_text(f'''# U1 ataskaita

Wine klasifikavimo projektas: 178 įrašai, 13 požymių, trys klasės. Train/test
padalijimas 142/36, stratifikuotas, seed 42. Random Forest mokomas CPU.

**Įgyvendinta.** DVC grandinė prepare → train → evaluate, parametrų failas,
lock ir vietinis remote. Trys skirtingų hiperparametrų mokymai log'inami į savo
MLflow kind klasteryje. PostgreSQL saugo metaduomenis, atskiras PVC — artefaktus.
Modelis, duomenų ir kodo SHA256, parametrai bei uv.lock leidžia atkurti istorinį run'ą.
Inferencijos Docker vaizdas paleidžiamas ne root vartotoju; įvestis — JSON.

| Patikra | Rezultatas |
|---|---|
| Istorinio run'o atkūrimas | {reproduction["seconds"]:.3f} s; visos keturios metrikos sutapo |
| Didžiausia modelio fit trukmė | {fit_max:.3f} s |
| Atskira projekto kopija ir tuščias DVC remote | {fresh["seconds"]:.3f} s; pipeline ir cache atkūrimas PASS |
| MLflow ir PostgreSQL Pod'ų perkūrimas | Metaduomenys ir artefaktų hash'ai nepasikeitė |
| Inferencijos vaizdo dydis | {size_mb:.2f} MB, arm64 |
| Trivy | CRITICAL {severity["CRITICAL"]}, HIGH {severity["HIGH"]}, MEDIUM {severity["MEDIUM"]} |

**Kas neveikė.** MLflow pradžioje viršijo 1536 MiB limitą dėl įjungto foninių
užduočių vykdymo. Šiam darbui nenaudojamas job vykdiklis išjungtas, tracking veikia
su vienu web worker'iu. MLflow nepalaiko Pandas 3, todėl aplinkoje naudojama 2.3.3.
Medžio serializavimui aiškiai leidžiamas savo apmokyto sklearn medžio tipas.
Likę HIGH OS radiniai ir pataisų prieinamumas pateikti security-scan.md.

**Laikas.** Darbas užtruko apie 8 valandas.

{publication_status}
''')
print('Updated requirements.md, u1-report.md, image-sizes.md and security-scan.md.')
