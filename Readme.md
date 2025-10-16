# Send Logs to Loki GitHub Action

The **Send Logs to Loki** GitHub Action collects logs from all jobs in a GitHub Actions workflow and sends them to a Loki instance. Logs are labeled with metadata like job names, job IDs, and custom labels, making them easily searchable and organized in Loki.

## Features

- **Log Aggregation**: Aggregates logs from all jobs in a workflow, including job-specific logs.
- **Custom Labels & Metadata**: Allows dynamic injection of custom labels and structured metadata.
- **Automatic Retry**: Automatically retries fetching logs if they are not immediately available.
- **Timestamp Parsing**: Parses timestamps from GitHub Actions logs and uses them in Loki requests, removing them from log messages to avoid duplication.
- **JSON Log Collapsing**: Automatically collapses multi-line pretty-printed JSON into single compact log lines.
- **JSON Wrapping**: Optionally wraps non-JSON log messages in a JSON object with a `message` key for consistent log format.

## Inputs

| Name                    | Description                                                   | Required | Default              |
| ----------------------- | --------------------------------------------------------------| -------- | -------------------- |
| `loki_endpoint`         | Loki push endpoint                                            | Yes      |                      |
| `labels`                | Custom labels for logs (comma-separated key=value pairs)      | No       | `job=github-actions` |
| `structured_metadata`   | Structured metadata for logs (comma-separated key=value pairs)| No       | `` (empty)           |
| `tenant`                | Tenant value for `X-Scope-OrgID` header                       | No       | `action-send-logs-to-loki` | 
| `github_token`          | GitHub token for API authentication                           | Yes      |                      |
| `max_retries`           | Maximum number of retry attempts for fetching logs per job    | No       | `5`                  |
| `retry_interval_seconds`| Interval in seconds between retry attempts                    | No       | `10`                 |
| `json_wrap`             | Wrap non-JSON logs with JSON message key                      | No       | `false`              |
| `collapse_json_logs`    | Collapse multi-line pretty-printed JSON into single log lines | No       | `true`               |

## Example Usage

```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.x'
- name: Send Logs to Loki
  uses: jeremydonahue/action-send-logs-to-loki@latest
  with:
    loki_endpoint: "https://loki.example.com"
    labels: "job=github-actions"
    structured_metadata: "run_id=${{ github.run_id }}"
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## How It Works

1. **Log Aggregation**: The action iterates over all jobs in the workflow using the GitHub Actions API.
2. **Log Retrieval**: Logs are fetched for completed jobs and skipped for jobs still in progress.
3. **Log Processing**:
   - **BOM Removal**: Strips UTF BOM characters that may appear in GitHub Actions logs.
   - **Timestamp Parsing**: Extracts timestamps (format: `2025-10-13T22:51:56.2115421Z`) from each log line and uses them for accurate event timing in Loki.
   - **JSON Collapsing** (optional): Collapses multi-line pretty-printed JSON objects into single compact lines when the opening `{` and closing `}` are alone on their lines.
   - **JSON Wrapping** (optional): Wraps non-JSON log messages in a JSON object for consistent format.
4. **Log Transmission**: Logs are sent to Loki with the specified labels and structured metadata.

## How to Configure

- **Add Custom Labels**: Use the `labels` input to include additional labels for your logs (these are indexed, so be aware of [cardinality](https://grafana.com/docs/loki/latest/get-started/labels/cardinality/)).
  - Example: `labels: "job=github-actions,env=production"`
- **Add Custom Metadata**: Use the `structured_metadata` input to include additional [structured metadata](https://grafana.com/docs/loki/latest/get-started/labels/structured-metadata/) for your logs. Cardinality is not a concern here.
  - Example: `structured_metadata: "run_id=${{ github.run_id }}"`
- **Loki Endpoint**: Specify the Loki instance URL with `loki_endpoint`.
- **Retry Configuration**: Use the `max_retries` and `retry_interval_seconds` inputs to control log fetch retry behavior.
- **JSON Log Collapsing**: Set `collapse_json_logs: "false"` to disable automatic collapsing of multi-line JSON. By default, this is enabled (`true`).
- **JSON Wrapping**: Set `json_wrap: "true"` to wrap non-JSON log messages in a JSON object with a `message` key. By default, this is disabled (`false`).

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