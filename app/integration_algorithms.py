"""Deterministic AIPMO algorithms independent of PMS vendor capabilities."""
from collections import defaultdict
from math import isfinite


def rollup_progress(packages, items, links):
    """Compute weighted WBS progress without double-counting mapped Plane work items.

    packages: [{id, weight, completion}], completion in [0, 1].
    items: [{id, completion}], completion in [0, 1].
    links: [{package_id, item_id, allocation}], allocation > 0.
    If a package has links, linked item completion replaces its manual completion.
    Shared items require explicit allocation across packages totaling <= 1.
    """
    def ratio(value):
        value = float(value)
        if not isfinite(value) or not 0 <= value <= 1:
            raise ValueError("completion must be finite and between 0 and 1")
        return value

    pmap = {}
    for p in packages:
        key = str(p["id"])
        weight = float(p["weight"])
        if key in pmap or not isfinite(weight) or weight <= 0:
            raise ValueError("duplicate package or invalid weight")
        pmap[key] = (weight, ratio(p["completion"]))
    imap = {}
    for item in items:
        key = str(item["id"])
        if key in imap:
            raise ValueError("duplicate item")
        imap[key] = ratio(item["completion"])
    by_package = defaultdict(list)
    by_item = defaultdict(float)
    pairs = set()
    for link in links:
        p, i = str(link["package_id"]), str(link["item_id"])
        allocation = float(link["allocation"])
        if p not in pmap or i not in imap:
            raise ValueError("unresolved mapping")
        if (p, i) in pairs or not isfinite(allocation) or allocation <= 0:
            raise ValueError("duplicate link or invalid allocation")
        pairs.add((p, i))
        by_item[i] += allocation
        by_package[p].append((i, allocation))
    if any(v > 1 + 1e-9 for v in by_item.values()):
        raise ValueError("shared item allocation exceeds 1")
    total = sum(w for w, _ in pmap.values())
    if not total:
        raise ValueError("no weighted packages")
    results = {}
    for p, (weight, manual) in pmap.items():
        mapped = by_package[p]
        completion = (sum(imap[i] * a for i, a in mapped) / sum(a for _, a in mapped)) if mapped else manual
        results[p] = round(completion, 8)
    return {"progress_pct": round(100 * sum(pmap[p][0] * c for p, c in results.items()) / total, 4),
            "package_completion": results}


def schedule_risk(tasks, today):
    """Deterministic schedule warnings, without claiming ML prediction."""
    from datetime import date
    now = date.fromisoformat(today)
    alerts = []
    for task in tasks:
        progress = float(task["completion"])
        if not isfinite(progress) or not 0 <= progress <= 1:
            raise ValueError("invalid completion")
        due = date.fromisoformat(task["due_date"])
        if progress < 1 and due < now:
            alerts.append({"id": str(task["id"]), "kind": "overdue", "days": (now - due).days})
        elif progress < 1 and due == now:
            alerts.append({"id": str(task["id"]), "kind": "due_today", "days": 0})
    return alerts
