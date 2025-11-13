# Changelog

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

## v0.0.3
- **Feature:** You can now send a custom message to Loki by setting the `message_to_loki` input (or `MESSAGE_TO_LOKI` environment variable). When this is set, the action will ignore all GitHub Actions logs and send only the provided message.
- **Improvement:** The Python script is now more modular and easier to maintain.
- **Documentation:** All usage instructions and examples have been updated to reflect the new feature.
