"""Project scope policy and deterministic incremental work-item filtering."""
from datetime import datetime, timezone
import os

def _parse_time(value):
    if not value:
        return None
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return parsed.astimezone(timezone.utc)

def check_project_access(project_key, allowed_projects=None):
    allowed = allowed_projects if allowed_projects is not None else os.environ.get("PMO_ALLOWED_PROJECTS", "")
    names = {item.strip() for item in allowed.split(",") if item.strip()}
    if not names or project_key not in names:
        raise PermissionError("project not authorized")
    return True

def changed_since(records, watermark=None, updated_key="updated"):
    since = _parse_time(watermark)
    result = []
    missing = []
    for record in records:
        value = record.get(updated_key)
        if not value:
            missing.append(record)
            continue
        changed = _parse_time(value)
        if since is None or changed > since:
            result.append(record)
    return {"changed": result, "missing_timestamp": missing,
            "next_watermark": max((r[updated_key] for r in result), default=watermark)}
