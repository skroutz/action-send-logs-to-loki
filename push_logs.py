import os
import json
import requests
import re
import time



def load_env():
    env = {}
    env["GITHUB_TOKEN"] = os.getenv("GITHUB_TOKEN")
    env["RUN_ID"] = os.getenv("RUN_ID")
    env["LOKI_ENDPOINT"] = os.getenv("LOKI_ENDPOINT")
    env["LABELS"] = os.getenv("LABELS", "job=github-actions")
    env["GITHUB_REPO"] = os.getenv("GITHUB_REPOSITORY")
    env["MAX_RETRIES"] = int(os.getenv("MAX_RETRIES", 5))
    env["RETRY_INTERVAL_SECONDS"] = int(os.getenv("RETRY_INTERVAL_SECONDS", 10))
    env["MESSAGE_TO_LOKI"] = os.getenv("MESSAGE_TO_LOKI")
    env["HEADERS"] = {"Authorization": f"Bearer {env['GITHUB_TOKEN']}", "Accept": "application/vnd.github.v3+json"}
    return env

def sanitize_labels(labels):
    """Sanitize labels to comply with Loki's label naming rules."""
    sanitized = {}
    for k, v in (item.split("=", 1) for item in labels.split(",") if "=" in item):
        # Replace invalid characters while preserving valid ones (ASCII letters, digits, _, :)
        key = re.sub(r"[^a-zA-Z0-9_:]", "_", k).lstrip("0123456789")
        if not key or not re.match(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$", key):
            raise ValueError(f"Invalid label key after sanitization: '{k}'")
        sanitized[key] = v
    return sanitized

def get_jobs(run_id, github_repo, headers):
    """Fetch all jobs metadata for the current workflow run."""
    print(f"Fetching job metadata for workflow run ID: {run_id}")
    jobs_url = f"https://api.github.com/repos/{github_repo}/actions/runs/{run_id}/jobs"
    response = requests.get(jobs_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch jobs: {response.text}")
    return response.json().get("jobs", [])

def fetch_job_logs(job_id, github_repo, headers):
    """Fetch logs for a specific job."""
    logs_url = f"https://api.github.com/repos/{github_repo}/actions/jobs/{job_id}/logs"
    response = requests.get(logs_url, headers=headers)
    if response.status_code == 200:
        return response.text.splitlines()
    elif response.status_code == 403:
        print(f"Logs not ready yet for job ID: {job_id}")
        return []
    else:
        print(f"Failed to fetch logs for job {job_id}: {response.status_code}")
        return []

def push_to_loki(logs, labels, loki_endpoint, job_name=None, job_id=None):
    """Push logs to Loki."""
    # Add job name and job ID as additional labels if provided
    if job_name:
        labels += f",job_name={job_name}"
    if job_id:
        labels += f",job_id={job_id}"

    # Sanitize labels before sending to Loki
    sanitized_labels = sanitize_labels(labels)

    payload = {
        "streams": [
            {
                "stream": sanitized_labels,
                "values": [[str(int(time.time() * 1e9)), log] for log in logs if log],  # Include timestamps
            }
        ]
    }
    print(f"Pushing logs to Loki: {loki_endpoint}")
    response = requests.post(f"{loki_endpoint}/loki/api/v1/push", json=payload)
    if response.status_code == 204:
        print("Logs successfully sent to Loki.")
    else:
        print(f"Failed to send logs to Loki: {response.status_code}, {response.text}")



def send_custom_message_to_loki(message, labels, loki_endpoint):
    print("MESSAGE_TO_LOKI is set. Sending only this message to Loki and skipping GitHub Actions logs.")
    push_to_loki([message], labels, loki_endpoint)

def send_github_logs_to_loki(env):
    jobs = get_jobs(env["RUN_ID"], env["GITHUB_REPO"], env["HEADERS"])
    for job in jobs:
        job_id = job.get("id")
        status = job.get("status")
        name = job.get("name")
        print(f"Processing job ID: {job_id} ({name}), Status: {status}")

        if status != "completed":
            print(f"Skipping job ID: {job_id} (status: {status})")
            continue

        logs_to_send = []
        for attempt in range(1, env["MAX_RETRIES"] + 1):
            print(f"Fetching logs for job ID: {job_id} (Attempt {attempt}/{env['MAX_RETRIES']})")
            logs = fetch_job_logs(job_id, env["GITHUB_REPO"], env["HEADERS"])
            if logs:
                logs_to_send.extend(logs)
                break  # Stop retrying once logs are fetched
            print(f"No logs available yet for job ID: {job_id}. Retrying in {env['RETRY_INTERVAL_SECONDS']} seconds...")
            time.sleep(env["RETRY_INTERVAL_SECONDS"])

        if logs_to_send:
            print(f"Sending {len(logs_to_send)} log lines to Loki for job {name}...")
            push_to_loki(logs_to_send, env["LABELS"], env["LOKI_ENDPOINT"], job_name=name)
        else:
            print(f"No logs to send for job {name}.")

def main():
    env = load_env()
    if env["MESSAGE_TO_LOKI"]:
        send_custom_message_to_loki(env["MESSAGE_TO_LOKI"], env["LABELS"], env["LOKI_ENDPOINT"])
    else:
        send_github_logs_to_loki(env)

if __name__ == "__main__":
    main()
