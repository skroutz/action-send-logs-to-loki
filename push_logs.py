import os
import json
import requests
import re
import time
from datetime import datetime

# Environment Variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
RUN_ID = os.getenv("RUN_ID")
LOKI_ENDPOINT = os.getenv("LOKI_ENDPOINT")
LABELS = os.getenv("LABELS", "job=github-actions")
TENANT = os.getenv("TENANT", "action-send-logs-to-loki")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
STRUCTURED_METADATA = os.getenv("STRUCTURED_METADATA", "")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))  # Defaults to 5 retries if not setup in the action
RETRY_INTERVAL_SECONDS = int(os.getenv("RETRY_INTERVAL_SECONDS", 10))  # Defaults to 10 seconds if not setup in the action
JSON_WRAP = os.getenv("JSON_WRAP", "false")
COLLAPSE_JSON_LOGS = os.getenv("COLLAPSE_JSON_LOGS", "true")

GITHUB_HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
LOKI_HEADERS = {"X-Scope-OrgID": TENANT}
structured_metadata = {k: v for k, v in [item.split("=", 1) for item in STRUCTURED_METADATA.split(",") if "=" in item]}

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

def parse_log_line(log_line):
    """Parse log line to extract timestamp and message.
    
    Expected format: '2025-10-13T22:51:56.2115421Z message'
    Returns: (timestamp_ns, message) tuple
    """
    # Strip BOM character if present (can appear on first line)
    log_line = log_line.lstrip('ï»¿')
    
    parts = log_line.split(" ", 1)
    timestamp_str = parts[0]
    message = parts[1]
    
    # Parse timestamp and convert to nanoseconds since epoch
    # Python < 3.11 doesn't support more than 6 decimal places for fractional seconds
    # GitHub Actions uses 7 decimal places, so we need to truncate. Also, we need to 
    # replace Z with +00:00 in the timestamp.
    timestamp_str = timestamp_str.rstrip("Z")[:-1] + "+00:00"
    dt = datetime.fromisoformat(timestamp_str)
    timestamp_ns = str(int(dt.timestamp() * 1e9))
    
    return timestamp_ns, message

def parse_logs(logs):
    """Parse logs to extract timestamp and message."""
    return [parse_log_line(log) for log in logs if log]

def wrap_log_with_json(log):
    """Wrap non-JSON log with JSON."""
    ts, message = log
    if message.startswith('{'):
        return log
    return ts, json.dumps({"message": message})

def wrap_logs_with_json(logs):
    """Wrap non-JSON logs with JSON."""
    return [wrap_log_with_json(log) for log in logs]

def collapse_json_logs(parsed_logs):
    """Collapse multi-line pretty-printed JSON into single log lines.
    
    Takes a list of (timestamp_ns, message) tuples and collapses any
    pretty-printed JSON objects into single lines. Only collapses JSON
    when the opening { and closing } are alone on their lines.
    """
    result = []
    json_buffer = []
    json_timestamp = None
    in_json_block = False
    
    for timestamp_ns, message in parsed_logs:
        stripped = message.strip()
        
        if not in_json_block and stripped == '{':
            # Start of JSON block (opening brace alone on line)
            json_timestamp = timestamp_ns
            json_buffer = [stripped]
            in_json_block = True
        elif in_json_block and stripped == '}':
            # End of JSON block (closing brace alone on line)
            json_buffer.append(stripped)
            
            # Collapse the JSON block
            collapsed = ' '.join(json_buffer)
            # Try to parse and re-serialize to ensure it's valid and compact
            try:
                parsed_json = json.loads(collapsed)
                collapsed = json.dumps(parsed_json, separators=(',', ':'))
            except json.JSONDecodeError:
                # If parsing fails, just use the joined string
                pass
            result.append((json_timestamp, collapsed))
            
            json_buffer = []
            json_timestamp = None
            in_json_block = False
        elif in_json_block:
            # Inside a JSON block
            json_buffer.append(stripped)
        else:
            # Regular log line
            result.append((timestamp_ns, message))
    
    # If there's an unclosed JSON block, add all lines as-is
    if json_buffer:
        for i, line in enumerate(json_buffer):
            if i == 0:
                result.append((json_timestamp, line))
            else:
                # We don't have timestamps for these lines, use the original timestamp
                result.append((json_timestamp, line))
    
    return result

def get_jobs(run_id):
    """Fetch all jobs metadata for the current workflow run."""
    print(f"Fetching job metadata for workflow run ID: {run_id}")
    jobs_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}/jobs"
    response = requests.get(jobs_url, headers=GITHUB_HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch jobs: {response.text}")
    return response.json().get("jobs", [])

def fetch_job_logs(job_id):
    """Fetch logs for a specific job."""
    logs_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/jobs/{job_id}/logs"
    response = requests.get(logs_url, headers=GITHUB_HEADERS)
    if response.status_code == 200:
        logs = response.text.splitlines()
        logs = parse_logs(logs)
        if COLLAPSE_JSON_LOGS == "true":
            logs = collapse_json_logs(logs)
        if JSON_WRAP == "true":
            logs = wrap_logs_with_json(logs)
        return logs
    elif response.status_code == 403:
        print(f"Logs not ready yet for job ID: {job_id}")
        return []
    else:
        raise Exception(f"Failed to fetch logs for job {job_id}: {response.status_code}")

def push_to_loki(logs, labels, job_name=None, job_id=None):
    """Push logs to Loki."""
    # Add job name and job ID as additional structured metadata if provided
    metadata = structured_metadata.copy()
    if job_name:
        metadata["job_name"] = job_name
    if job_id:
        metadata["job_id"] = job_id

    # Sanitize labels before sending to Loki
    sanitized_labels = sanitize_labels(labels)
    
    payload = {
        "streams": [
            {
                "stream": sanitized_labels,
                "values": [[timestamp_ns, message, metadata] for timestamp_ns, message in logs],
            }
        ]
    }
    print(f"Pushing logs to Loki: {LOKI_ENDPOINT}")
    response = requests.post(f"{LOKI_ENDPOINT}/loki/api/v1/push", json=payload, headers=LOKI_HEADERS)
    if response.status_code == 204:
        print("Logs successfully sent to Loki.")
    else:
        raise RuntimeError(f"Failed to send logs to Loki: {response.status_code}, {response.text}")

def main():
    jobs = get_jobs(RUN_ID)
    for job in jobs:
        job_id = job.get("id")
        status = job.get("status")
        name = job.get("name")
        print(f"Processing job ID: {job_id} ({name}), Status: {status}")

        if status != "completed":
            print(f"Skipping job ID: {job_id} (status: {status})")
            continue

        logs_to_send = []
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"Fetching logs for job ID: {job_id} (Attempt {attempt}/{MAX_RETRIES})")
            logs = fetch_job_logs(job_id)
            if logs:
                logs_to_send.extend(logs)
                break  # Stop retrying once logs are fetched
            print(f"No logs available yet for job ID: {job_id}. Retrying in {RETRY_INTERVAL_SECONDS} seconds...")
            time.sleep(RETRY_INTERVAL_SECONDS)

        if logs_to_send:
            print(f"Sending {len(logs_to_send)} log lines to Loki for job {name}...")
            push_to_loki(logs_to_send, LABELS, job_name=name)
        else:
            print(f"No logs to send for job {name}.")

if __name__ == "__main__":
    main()
