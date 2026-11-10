"""Load test for the inference API: N concurrent users POST examples/wine.json to /predict."""
import json
from pathlib import Path

from locust import HttpUser, between, task

EXAMPLE = json.loads((Path(__file__).resolve().parents[1] / "examples/wine.json").read_text())


class ApiUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def predict(self):
        self.client.post("/predict", json=EXAMPLE)
