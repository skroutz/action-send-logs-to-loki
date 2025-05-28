import requests
import time
from utils import sanitize_labels
from config import LOKI_ENDPOINT

def push_to_loki(logs: list[str], labels: str, job_name: str = None, job_id: str = None) -> None:
    if job_name:
        labels += f",job_name={job_name}"
    if job_id:
        labels += f",job_id={job_id}"
    sanitized_labels = sanitize_labels(labels)
    payload = {
        "streams": [
            {
                "stream": sanitized_labels,
                "values": [[str(int(time.time() * 1e9)), log] for log in logs if log],
            }
        ]
    }
    response = requests.post(f"{LOKI_ENDPOINT}/loki/api/v1/push", json=payload)
    if response.status_code != 204:
        raise RuntimeError(f"Failed to send logs to Loki: {response.status_code}, {response.text}")
