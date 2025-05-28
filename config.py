import os

LANGUAGE = os.getenv("PROJECT_LANGUAGE", "en")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
RUN_ID = os.getenv("RUN_ID")
LOKI_ENDPOINT = os.getenv("LOKI_ENDPOINT")
LABELS = os.getenv("LABELS", "job=github-actions")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))
RETRY_INTERVAL_SECONDS = int(os.getenv("RETRY_INTERVAL_SECONDS", 10))
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
