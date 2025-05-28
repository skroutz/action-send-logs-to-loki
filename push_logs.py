from config import RUN_ID, LABELS, MAX_RETRIES, RETRY_INTERVAL_SECONDS, LANGUAGE
from github_api import get_jobs, fetch_job_logs
from loki_client import push_to_loki
# Messages for Greek and English languages for better personalization and understanding of the project!
MESSAGES = {
    "en": {
        "fetching_jobs": "Fetching job metadata for workflow run ID: {run_id}",
        "processing_job": "Processing job ID: {job_id} ({name}), Status: {status}",
        "skipping_job": "Skipping job ID: {job_id} (status: {status})",
        "fetching_logs": "Fetching logs for job ID: {job_id} (Attempt {attempt}/{max_retries})",
        "no_logs": "No logs available yet for job ID: {job_id}. Retrying in {interval} seconds...",
        "sending_logs": "Sending {count} log lines to Loki for job {name}...",
        "logs_sent": "Logs successfully sent to Loki.",
        "logs_failed": "Failed to send logs to Loki: {error}"
    },
    "el": {
        "fetching_jobs": "Ανάκτηση μεταδεδομένων εργασίας για το run ID: {run_id}",
        "processing_job": "Επεξεργασία εργασίας ID: {job_id} ({name}), Κατάσταση: {status}",
        "skipping_job": "Παράλειψη εργασίας ID: {job_id} (κατάσταση: {status})",
        "fetching_logs": "Ανάκτηση logs για εργασία ID: {job_id} (Προσπάθεια {attempt}/{max_retries})",
        "no_logs": "Δεν υπάρχουν logs ακόμη για εργασία ID: {job_id}. Προσπάθεια ξανά σε {interval} δευτερόλεπτα...",
        "sending_logs": "Αποστολή {count} γραμμών logs στο Loki για την εργασία {name}...",
        "logs_sent": "Τα logs εστάλησαν επιτυχώς στο Loki.",
        "logs_failed": "Αποτυχία αποστολής logs στο Loki: {error}"
    }
}

def get_message(key: str, **kwargs) -> str:
    lang = LANGUAGE if LANGUAGE in MESSAGES else "en"
    return MESSAGES[lang][key].format(**kwargs)

# Thi sis the main function that does the entire process
def main() -> None:
    try:
        jobs = get_jobs(RUN_ID)
    except Exception as e:
        print(get_message("logs_failed", error=str(e)))
        return
    for job in jobs:
        job_id = job.get("id")
        status = job.get("status")
        name = job.get("name")
        print(get_message("processing_job", job_id=job_id, name=name, status=status))
        if status != "completed":
            print(get_message("skipping_job", job_id=job_id, status=status))
            continue
        logs_to_send = []
        for attempt in range(1, MAX_RETRIES + 1):
            print(get_message("fetching_logs", job_id=job_id, attempt=attempt, max_retries=MAX_RETRIES))
            try:
                logs = fetch_job_logs(job_id)
            except Exception as e:
                print(get_message("logs_failed", error=str(e)))
                logs = []
            if logs:
                logs_to_send.extend(logs)
                break
            print(get_message("no_logs", job_id=job_id, interval=RETRY_INTERVAL_SECONDS))
            import time
            time.sleep(RETRY_INTERVAL_SECONDS)
        if logs_to_send:
            print(get_message("sending_logs", count=len(logs_to_send), name=name))
            try:
                push_to_loki(logs_to_send, LABELS, job_name=name, job_id=job_id)
                print(get_message("logs_sent"))
            except Exception as e:
                print(get_message("logs_failed", error=str(e)))

if __name__ == "__main__":
    main()

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
