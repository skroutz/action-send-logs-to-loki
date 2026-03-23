# Send Logs to Loki GitHub Action

The **Send Logs to Loki** GitHub Action collects logs from all jobs in a GitHub Actions workflow and sends them to a Loki instance. Logs are labeled with metadata like job names, job IDs, and custom labels, making them easily searchable and organized in Loki.

## Features

- Aggregates logs from all jobs in a workflow, including job-specific logs.
- Allows dynamic injection of custom labels.
- Automatically retries fetching logs if they are not immediately available.
- Send one or more custom messages to Loki, bypassing GitHub Actions logs.

## Inputs

| Name                    | Description                                                | Required | Default              |
| ----------------------- | -----------------------------------------------------------| -------- | -------------------- |
| `loki_endpoint`         | Loki push endpoint                                         | Yes      |                      |
| `labels`                | Custom labels for logs (comma-separated key=value pairs)   | No       | `job=github-actions` |
| `github_token`          | GitHub token for API authentication                        | Yes      |                      |
| `max_retries`           | Maximum number of retry attempts for fetching logs per job | No      |  5                   |
| `retry_interval_seconds`| Interval in seconds between retry attempts                 | No      |  10                  |
| `message_to_loki`       | Custom message(s) to send directly to Loki (skips job logs). Supports multiple lines — each line is sent as a separate log entry. Optionally append per-line labels with a pipe separator: `message | key=value,key=value` (spaces around `\|` are optional). | No      |                      |

## Example Usage

```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.x'
- name: Send Logs to Loki
  uses: skroutz/action-send-logs-to-loki@latest
  with:
    loki_endpoint: "https://loki.example.com"
    labels: "job=github-actions,run_id=${{ github.run_id }}"
    github_token: ${{ secrets.GITHUB_TOKEN }}
    message_to_loki: |
      Deployment started by ${{ github.actor }}
      Version: ${{ github.sha }}
```

## How It Works

1. **Custom Message Mode**: If the `message_to_loki` input (or `MESSAGE_TO_LOKI` env var) is set, the action sends only these messages to Loki and skips all GitHub Actions logs. Each non-empty line is treated as a separate log entry.
2. **Log Aggregation**: Otherwise, the action iterates over all jobs in the workflow using the GitHub Actions API.
3. **Log Retrieval**: Logs are fetched for completed jobs and skipped for jobs still in progress.
4. **Log Transmission**: Logs are sent to Loki with the specified labels.

## How to Configure

- **Send Custom Messages**: Set the `message_to_loki` input (or `MESSAGE_TO_LOKI` environment variable) to send one or more messages to Loki, ignoring all job logs. Use a multiline YAML string to send multiple entries. Lines sharing the same label set are grouped into a single Loki push request; lines with different label sets result in one push request per distinct label set.
  - Example: `message_to_loki: "Manual trigger by admin"`
  - Multiline example:
    ```yaml
    message_to_loki: |
      Manual trigger by admin
      Environment: production
    ```
  - Per-message labels example:
    ```yaml
    message_to_loki: |
      Deployment started | env=production,service=api
      Cache warmed up | env=production,service=cache
      A message with only global labels
    ```
- **Add Custom Labels**: Use the `labels` input to include additional metadata for your logs.
  - Example: `labels: "job=github-actions,env=production"`
- **Loki Endpoint**: Specify the Loki instance URL with `loki_endpoint`.
- **Retry Configuration**: Use the `max_retries` and `retry_interval_seconds` inputs to control log fetch retry behavior.

By default, `job_name` are automatically added as labels for each job. (Be mindful of cardinality!)

## Dependencies

This action requires **Python 3**. It is recommended to use the [official GitHub action](https://github.com/actions/setup-python) to ensure the correct Python version is installed:

```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.x'
```

## Known Limitations

- Logs are only fetched for completed jobs. Logs for in-progress jobs will be skipped.
- Timestamps in Loki are processed as arrived. Therefore Loki timestamps are injected at the time of transmission, along with GitHub Actions real Timestamps.
