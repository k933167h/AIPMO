"""Read-only normalization of GANTT-AX v7.3 exported project state."""
from datetime import date
from typing import Any

def normalize_project(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("project"), dict) or not isinstance(payload.get("tasks"), list):
        raise ValueError("GANTT-AX state requires project object and tasks array")
    project = payload["project"]
    tasks = []
    ids = set()
    for t in payload["tasks"]:
        if not isinstance(t, dict) or not isinstance(t.get("id"), str) or not t["id"] or t["id"] in ids:
            raise ValueError("invalid or duplicate task id")
        ids.add(t["id"])
        start = t.get("start")
        if start:
            date.fromisoformat(start)
        progress = float(t.get("progress", 0))
        duration = float(t.get("duration", 0))
        if not 0 <= progress <= 100 or duration < 0:
            raise ValueError("invalid progress or duration")
        tasks.append({"external_id": t["id"], "parent_external_id": t.get("parentId"), "name": t.get("name", ""), "start": start, "duration_days": duration, "progress_pct": progress, "owner": t.get("owner", ""), "type": t.get("type", "task"), "planned_man_days": t.get("manDay", 0), "actual_man_days": t.get("actualManDay", 0), "predecessors": t.get("predecessors", [])})
    for t in tasks:
        if t["parent_external_id"] is not None and t["parent_external_id"] not in ids:
            raise ValueError("missing parent")
        for dep in t["predecessors"]:
            if not isinstance(dep, dict) or dep.get("id") not in ids or dep.get("type", "FS") not in {"FS", "SS", "FF", "SF"}:
                raise ValueError("invalid predecessor")
    return {"source": "GANTT-AX", "project": {"name": project.get("name"), "code": project.get("code"), "manager": project.get("manager"), "start_date": project.get("startDate")}, "tasks": tasks, "extensions": {k: payload[k] for k in ("baseline", "holidays", "vbs", "fp", "resources", "governance", "ccpm", "monteCarlo", "ax", "quality", "portfolio", "pmo", "portfolioPlanning", "gateReadiness", "assurance", "aiEvaluation", "runtime", "continuousAssurance") if k in payload}}
