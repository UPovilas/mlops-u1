import os
import time
from urllib.request import urlopen

uri = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5002")
deadline = time.monotonic() + 60
while True:
    try:
        with urlopen(uri + "/health", timeout=2) as response:
            if response.status == 200:
                print(f"MLflow ready: {uri}")
                break
    except OSError:
        pass
    if time.monotonic() >= deadline:
        raise SystemExit(f"MLflow did not become ready: {uri}")
    time.sleep(1)
