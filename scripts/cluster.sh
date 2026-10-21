#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
mkdir -p .state/cluster
KUBECONFIG_FILE="$ROOT/.state/kubeconfig"
KUBECTL="$ROOT/.state/bin/kubectl"
if [ ! -x "$KUBECTL" ]; then
  bash scripts/install-tools.sh
fi
k() { "$KUBECTL" --kubeconfig "$KUBECONFIG_FILE" -n wine-u1 "$@"; }

case "${1:-status}" in
  up)
    docker info >/dev/null
    if ! kind get clusters 2>/dev/null | grep -qx wine-u1; then
      kind create cluster --name wine-u1 --config k8s/kind-config.yaml --kubeconfig "$KUBECONFIG_FILE" --wait 120s
    else
      kind export kubeconfig --name wine-u1 --kubeconfig "$KUBECONFIG_FILE"
    fi
    docker build -f docker/Dockerfile.mlflow -t wine-u1-mlflow:3.15.2 .
    kind load docker-image wine-u1-mlflow:3.15.2 --name wine-u1
    k apply -f k8s/namespace.yaml
    if ! k get secret postgres >/dev/null 2>&1; then
      if [ ! -f .state/cluster/postgres.env ]; then
        python3 - <<'PY'
import os
import secrets
from pathlib import Path
path = Path('.state/cluster/postgres.env')
path.write_text('POSTGRES_USER=mlflow\nPOSTGRES_DB=mlflow\nPOSTGRES_PASSWORD=' + secrets.token_urlsafe(32) + '\n')
os.chmod(path, 0o600)
PY
      fi
      k create secret generic postgres --from-env-file=.state/cluster/postgres.env
    fi
    k apply -f k8s/postgres.yaml
    k rollout status deployment/postgres --timeout=180s
    k apply -f k8s/mlflow.yaml
    k rollout restart deployment/mlflow
    k rollout status deployment/mlflow --timeout=180s
    k get deployments,services,pvc
    ;;
  forward)
    trap 'exit 0' INT TERM
    while true; do
      k port-forward --address 127.0.0.1 service/mlflow 5002:5000 || true
      sleep 2
    done
    ;;
  status)
    k get pods,deployments,services,pvc
    ;;
  *)
    echo 'Usage: bash scripts/cluster.sh {up|forward|status}' >&2
    exit 2
    ;;
esac
