# U2 ataskaita — Wine MLOps

## Architektūra

```
git push ─▶ CI (GitHub, ubuntu-latest): ruff → pytest → API vaizdas į GHCR (sha-<12>)
               │ žalias
               ▼
           CD (self-hosted runner, šis Mac): dvc pull → mokymo Job klasteryje → API set image
               │
kind klasteris (namespace wine-u1)
  Job wine-train: prepare → hpo → train → evaluate → quality_gate → register
     │ env: ConfigMap train-config, Secret mlflow-auth; params.yaml: ConfigMap train-params
     ▼
  MLflow (Service mlflow:5000, Postgres + PVC) ── registras: wine-classifier @champion
     ▲
  Deployment wine-api (FastAPI) ── krauna models:/wine-classifier@champion starto metu
     │ HPA 1–3 Pod'ai (CPU 50 %), Service wine-api:80
```

- **HPO:** Optuna, 10 bandymų, kiekvienas nested MLflow run'as po tėviniu `hpo`; tikslas OOB accuracy (test lieka vertinimui). Geriausi parametrai → `models/best_params.json` → `train.py`.
- **Registras:** `register.py` po `evaluate`: kiekvienas įvertintas modelis tampa nauja versija; `@champion` perkeliamas tik jei test accuracy ≥ dabartinio champion.
- **Kokybės vartas:** `quality_gate.py` prieš `register.py`; accuracy < 0.85 → `exit 1` → Job `Failed` → CD raudonas, registracija ir deploy nevyksta.
- **API:** modelis kraunamas vieną kartą starto metu; jei registras nepasiekiamas, procesas nulūžta (fail fast), readiness `/health` nepraeina ir srautas nesiunčiamas.

## Matavimai

| Ką | Sąlygos | Rezultatas |
|---|---|---|
| `/predict` latency | Locust, 10 vartotojų, 30 s, per port-forward (1 Pod'as) | p50 9 ms, p95 19 ms, p99 170 ms, ~32 req/s, 0 klaidų |
| `/predict` latency + HPA | Locust Job klasteryje, 40 vartotojų, 120 s, 3 Pod'ai | p50 4 ms, p95 8 ms, p99 17 ms, ~129 req/s, 0 klaidų |
| Srauto pasiskirstymas | tas pats testas | Pod'ai: 5766 / 3502 / 6203 užklausos |
| Kokybės vartas | žalias / raudonas CD | accuracy 1.0000 / 0.6389 (slenkstis 0.85) |
| API vaizdas | `docker images` | 476 MB, UID 10001 |

Pastabos: per `port-forward` visas srautas eina į vieną Pod'ą, todėl HPA efektas matuotas tik klasteryje. Pirmame klasterio bandyme HPA buvo sumažinęs iki 1 Pod'o, ir 40 keep-alive ryšių „prilipo“ prie jo (Service balansuoja ryšius, ne užklausas); antrame bandyme 3 Pod'ai jau egzistavo. Įrodymai: `docs/load/`.

## CI/CD įrodymai

| Paleidimas | Rezultatas |
|---|---|
| CI 42591874555 | žalias (test + image) |
| CD 42691090584 | žalias: `gate: pass accuracy=1.0000`, `wine-classifier v7`, API atnaujintas |
| CD 42699733765 | **raudonas**: `params.yaml` priverstas vienas kelmas → `gate: fail accuracy=0.6389 < threshold=0.8500`; naujos versijos nėra, `@champion` liko v7, API nepakeistas |
| CD 42701200040 | žalias po grąžinimo: `v8`, `@champion` → v8 |

## Rollback

API modelį ima iš alias'o, todėl `kubectl rollout undo` grąžintų tik vaizdą, o ne modelį. Rollback:

```bash
MLFLOW_TRACKING_URI=http://127.0.0.1:5002 uv run python -c "import mlflow; mlflow.MlflowClient().set_registered_model_alias('wine-classifier', 'champion', '7')"
.state/bin/kubectl --kubeconfig .state/kubeconfig -n wine-u1 rollout restart deployment/wine-api
```

Atlikta 2026-11-09: `@champion` v8 → v7, naujas Pod'as `wine-api-745998b7cc-t4b9h` pakrovė v7 (`Application startup complete`).

## Žinomi apribojimai

- MLflow serveris be autentifikacijos; Secret `mlflow-auth` mechanizmas paruoštas (Job gauna `MLFLOW_TRACKING_USERNAME/PASSWORD`), bet serveris jų netikrina.
- CD veikia tik kai šis Mac (self-hosted runner, Docker, kind) įjungtas; DVC saugykla vietinė.
- Test rinkinys mažas (36 eilutės): viena klaida = 2,8 % accuracy, todėl slenkstis 0.85, ne arti 1.0.
