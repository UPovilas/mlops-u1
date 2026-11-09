"""Quality gate: stop the pipeline (exit 1) before register.py if the model is not good enough."""
import json
import sys

from common import ROOT, params


def main():
    accuracy = json.loads((ROOT / "metrics.json").read_text())["accuracy"]
    threshold = params()["gate"]["min_accuracy"]
    if accuracy < threshold:
        print(f"gate: fail accuracy={accuracy:.4f} < threshold={threshold:.4f}")
        sys.exit(1)
    else:
        print(f"gate: pass accuracy={accuracy:.4f} >= threshold={threshold:.4f}")


if __name__ == "__main__":
    main()
