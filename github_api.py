import requests
from config import GITHUB_REPO, HEADERS
# Fetch all jobs metadata for the current workflow run
def get_jobs(run_id: str) -> list[dict]:
    jobs_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}/jobs"
    response = requests.get(jobs_url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch jobs: {response.text}")
    return response.json().get("jobs", [])
# Fetch logs for a specific job
def fetch_job_logs(job_id: str) -> list[str]:
    logs_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/jobs/{job_id}/logs"
    response = requests.get(logs_url, headers=HEADERS)
    if response.status_code == 200:
        return response.text.splitlines()
    elif response.status_code == 403:
        return []
    else:
        raise Exception(f"Failed to fetch logs for job {job_id}: {response.status_code}")
