# Wine MLOps — U1

Random Forest modelis pagal 13 cheminių požymių priskiria vyną vienai iš trijų klasių.
Duomenys — `sklearn.datasets.load_wine` (178 įrašai, 142 mokymui, 36 testui).

Projektas: DVC pipeline'as `prepare → train → evaluate`, MLflow serveris lokaliame
kind klasteryje (PostgreSQL + artefaktų PVC) ir inferencijos Docker vaizdas GHCR.

- Repozitorija: https://github.com/UPovilas/mlops-u1, pateikimo tag'as `u1-final`
- Reikalavimai: [docs/requirements.md](docs/requirements.md)
- Ataskaita: [docs/u1-report.md](docs/u1-report.md)

## Ko reikia

- macOS (arm64) arba Linux, Docker (rekomenduoju ≥8 GB RAM Docker'iui)
- Git, Python 3.12, [uv](https://docs.astral.sh/uv/), kind 0.33.0, Trivy
- GHCR publikavimui — GitHub CLI (`gh`)

kubectl atskirai diegti nereikia: `install-tools.sh` parsisiunčia v1.34.11 į `.state/bin/`
ir patikrina jo SHA256. Visos komandos vykdomos projekto šaknyje.

## Paleidimas nuo nulio

1. Priklausomybės, įrankiai ir duomenys:

   ```bash
   uv sync --frozen
   bash scripts/install-tools.sh
   uv run --frozen python scripts/bootstrap.py
   ```

   `bootstrap.py` sukuria DVC remote `../mlops-u1-dvc-store`. Jei jis tuščias,
   CSV sugeneruojamas iš scikit-learn, patikrinamas pagal `.dvc` MD5 ir įkeliamas į remote.

2. Klasteris ir MLflow:

   ```bash
   bash scripts/cluster.sh up
   ```

   Sukuriamas kind klasteris `wine-u1`, namespace `wine-u1`, PostgreSQL ir MLflow.
   Komandą galima kartoti — PVC ir duomenys išlieka.

3. Atskirame terminale paleisti port-forward ir palikti veikti:

   ```bash
   bash scripts/cluster.sh forward
   ```

4. Mokymai (trys run'ai: 10 medžių / gylis 2, 50 / 4, 100 / neribotas):

   ```bash
   export MLFLOW_TRACKING_URI=http://127.0.0.1:5002
   uv run --frozen python scripts/wait-mlflow.py
   uv run --frozen python scripts/experiments.py
   uv run --frozen dvc push
   ```

Jei projektas gautas ZIP archyvu (be `.git`), prieš 1 žingsnį paleisti `git init -b main`.

## Kur žiūrėti rezultatus

| Kas | Kur |
|---|---|
| MLflow UI | http://127.0.0.1:5002, eksperimentas `wine-u1` |
| Run'ų sąrašas su parametrais ir metrikomis | `docs/runs.json` |
| Paskutinio `dvc repro` metrikos | `metrics.json` |
| Reprodukcijos rezultatas | `docs/reproduction.json` |
| Docker vaizdo dydis ir Trivy | `docs/image-sizes.md`, `docs/security-scan.md`, `docs/trivy.json` |
| Klasterio būsena | `bash scripts/cluster.sh status` |

## Portai ir prisijungimai

| Paslauga | Adresas | Saugykla |
|---|---|---|
| MLflow | `127.0.0.1:5002` → Service `mlflow:5000` | PVC `mlflow-artifacts` (`/mlflow/artifacts`) |
| PostgreSQL | `postgres:5432`, tik klasterio viduje | PVC `postgres-data` |
| Kubernetes API | `.state/kubeconfig` | — |

- MLflow be autentifikacijos; port-forward klauso tik `127.0.0.1`.
- PostgreSQL slaptažodis sugeneruojamas per `cluster.sh up` ir laikomas Kubernetes
  Secret `postgres` bei `.state/cluster/postgres.env` (failas ne Git'e). Esamai DB jo nekeisti.
- Ištrynus Pod'ą duomenys išlieka; ištrynus visą kind klasterį — dingsta.

## Pipeline ir parametrai

```bash
uv run --frozen dvc repro
uv run --frozen dvc status
```

`params.yaml` — padalijimo ir modelio parametrai, `dvc.lock` — jų reikšmės ir failų hash'ai.
Git saugo kodą ir `.dvc` pointer'ius, DVC — CSV ir `model.pkl`, `uv.lock` — Python versijas.

Pakeitus `train.n_estimators` persileidžia `train` ir `evaluate`, `prepare` praleidžiamas.
Pakeitus tik `MLFLOW_TRACKING_URI`, DVC nieko neperskaičiuoja — tada `dvc repro --force`.

## Istorinio run'o atkūrimas

```bash
uv run --frozen python scripts/reproduce.py RUN_ID
```

Kiekvienas run'as MLflow turi `provenance.json` ir `source.tar.gz` (kodas, parametrai,
duomenys, `uv.lock`). Skriptas patikrina kodo ir duomenų SHA256, laikiname kataloge
paleidžia tą versiją su jos `uv.lock`, palygina keturias metrikas ir išmatuoja laiką.
Esami failai nepakeičiami, naujas run'as gauna žymą `reproduces`.

## Docker vaizdas

```bash
uv run --frozen python scripts/build-image.py
uv run --frozen python scripts/scan-image.py
```

`docker/Dockerfile` — inferencijos CLI: nuskaito JSON, išveda prognozes ir baigia darbą.
Viduje modelis ir ta pati scikit-learn versija kaip mokant, vartotojas `10001`.
Be argumentų naudoja `examples/wine.json`; savo failui:

```bash
docker run --rm --network none -v /absolute/path/input.json:/input.json:ro IMAGE --input /input.json
```

Publikuotas vaizdas ir jo digest — `docs/publication.json`.

## Patikros ir publikavimas

```bash
uv run --frozen python scripts/verify.py
uv run --frozen python scripts/verify-persistence.py
uv run --frozen python scripts/package.py
uv run --frozen python scripts/verify-fresh-start.py
uv run --frozen python scripts/reports.py
```

- `verify.py` — DVC, run'ai klasteryje, modelio parsisiuntimas, reprodukcija, konteineris
- `verify-persistence.py` — perkuria MLflow ir PostgreSQL Pod'us ir lygina run'o duomenis
- `verify-fresh-start.py` — pilnas paleidimas švarioje projekto kopijoje su tuščiu DVC remote
- `reports.py` — atnaujina `docs/` ataskaitas iš patikrų rezultatų

`bash scripts/publish.sh` (tik su švaria Git būsena) pakartoja mokymus, sukuria ir
nuskenuoja `sha-<commit>` vaizdą ir įkelia jį į GHCR. `scripts/package.py` sukuria
`dist/wine-u1.zip` be aplinkos, cache ir prisijungimų.

## Struktūra

```
src/       prepare, train, evaluate, predict
scripts/   klasteris, eksperimentai, reprodukcija, patikros, publikavimas
docker/    inferencijos ir MLflow Dockerfile'ai
k8s/       kind konfigūracija, namespace, PostgreSQL, MLflow
docs/      reikalavimai, ataskaita, matavimai
```

Naudota kurso medžiaga: [docs/sources.md](docs/sources.md).
