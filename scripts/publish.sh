#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
  echo 'Review and commit the project before publishing a sha-<commit> image.' >&2
  exit 1
fi
export MLFLOW_TRACKING_URI=http://127.0.0.1:5002
uv run --frozen python scripts/wait-mlflow.py
uv run --frozen python scripts/experiments.py
uv run --frozen python scripts/build-image.py
uv run --frozen python scripts/scan-image.py
OWNER=$(gh api user --jq '.login | ascii_downcase')
COMMIT=$(git rev-parse --short=12 HEAD)
IMAGE="ghcr.io/$OWNER/wine-u1:sha-$COMMIT"
gh auth token | docker login ghcr.io -u "$OWNER" --password-stdin
docker tag "wine-u1-inference:sha-$COMMIT" "$IMAGE"
docker push "$IMAGE"
docker image inspect "$IMAGE" --format '{{json .RepoDigests}}' > docs/registry-digests.json
echo "$IMAGE"
