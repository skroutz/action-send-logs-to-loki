# Changelog

## [v0.0.5] - 2026-09-03

### Added

- Set up Python with `actions/setup-python` before installing dependencies and sending logs.
- Added the configurable `python_version` input, defaulting to Python `3.12`.

### Changed

- Use the configured `python` interpreter consistently for dependency installation and log sending.

## [v0.0.4] - 2026-03-23

### Added

- `message_to_loki` now supports multiline strings; each non-empty line is sent as a separate log
  entry.
- Per-line label overrides via a pipe separator: `message | key=value,key=value`.

### Changed

- Lines sharing the same label set are grouped into a single Loki push request; distinct label sets
  result in separate push requests.
- Original line content (including leading/trailing whitespace) is preserved when sending messages
  to Loki.
- Updated documentation and usage examples to reflect the new behaviour.

## [v0.0.3] - 2025-11-13
### Added
- Support for `message_to_loki` input and `MESSAGE_TO_LOKI` environment variable. If set, the action sends only this message to Loki and skips all GitHub Actions logs.
- Updated documentation and usage examples to reflect the new feature.
- Modularized the Python script for better maintainability.

### Changed
- `action.yml` now includes the `message_to_loki` input and passes it to the script.
- README updated to document the new input and usage.

---

# Release Notes

## v0.0.5

- **Feature:** Python is set up automatically before the action runs, with the version configurable
  through the new `python_version` input and a default of `3.12`.
- **Improvement:** Dependencies and the log-sending script now run through the configured Python
  interpreter for consistent behavior across runners.

## v0.0.4

- **Feature:** `message_to_loki` now accepts multiline strings. Each non-empty line is treated as a
  separate log entry, removing the need to call the action N times for N messages. Original message
  content is preserved — leading/trailing whitespace is no longer stripped from log entries.
- **Feature:** Per-line label overrides using a pipe separator (`message | key=value,key=value`).
  Lines with the same labels are batched into a single Loki push request.

## v0.0.3
- **Feature:** You can now send a custom message to Loki by setting the `message_to_loki` input (or `MESSAGE_TO_LOKI` environment variable). When this is set, the action will ignore all GitHub Actions logs and send only the provided message.
- **Improvement:** The Python script is now more modular and easier to maintain.
- **Documentation:** All usage instructions and examples have been updated to reflect the new feature.
