import re
# Sanitize labels to comply with Loki's label naming rules
def sanitize_labels(labels: str) -> dict:
    sanitized = {}
    for k, v in (item.split("=", 1) for item in labels.split(",") if "=" in item):
        key = re.sub(r"[^a-zA-Z0-9_:]", "_", k).lstrip("0123456789")
        if not key or not re.match(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$", key):
            raise ValueError(f"Invalid label key after sanitization: '{k}'")
        sanitized[key] = v
    return sanitized
