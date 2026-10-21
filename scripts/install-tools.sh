#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .state/bin
case "$(uname -s)" in
  Darwin) system=darwin ;;
  Linux) system=linux ;;
  *) echo 'Supported systems: macOS and Linux.' >&2; exit 1 ;;
esac
case "$(uname -m)" in
  arm64|aarch64) architecture=arm64 ;;
  x86_64) architecture=amd64 ;;
  *) echo 'Supported architectures: arm64 and amd64.' >&2; exit 1 ;;
esac
url="https://dl.k8s.io/release/v1.34.11/bin/$system/$architecture/kubectl"
curl -fsSL --retry 2 "$url" -o .state/bin/kubectl
curl -fsSL --retry 2 "$url.sha256" -o .state/bin/kubectl.sha256
python3 - <<'PY'
import hashlib
from pathlib import Path
binary = Path('.state/bin/kubectl')
expected = Path('.state/bin/kubectl.sha256').read_text().strip()
if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
    raise SystemExit('kubectl checksum mismatch')
binary.chmod(0o755)
PY
.state/bin/kubectl version --client
