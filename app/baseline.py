"""Compare a dated CPM forecast against an explicitly supplied approved baseline."""
from datetime import date

def compare_baseline(forecast, baseline):
    """Date variance in calendar days; positive values mean delay."""
    if not isinstance(baseline,dict):
        raise ValueError("baseline must be an object")
    if baseline.get("approval_status")!="APPROVED":
        raise ValueError("baseline must be approved")
    tasks=baseline.get("tasks")
    if not isinstance(tasks,list):
        raise ValueError("baseline tasks must be a list")
    indexed={}
    for task in tasks:
        if not isinstance(task,dict) or not isinstance(task.get("id"),str) or not task["id"] or task["id"] in indexed:
            raise ValueError("invalid or duplicate baseline task id")
        indexed[task["id"]]=task
    rows=[]
    for task in forecast.get("tasks",[]):
        tid=task["id"]
        base=indexed.get(tid)
        if base is None:
            rows.append({"id":tid,"baseline_status":"NEW","start_variance_days":None,"finish_variance_days":None})
            continue
        try:
            planned_start=date.fromisoformat(base["start_date"])
            planned_finish=date.fromisoformat(base["finish_date"])
            forecast_start=date.fromisoformat(task["early_start_date"])
            forecast_finish=date.fromisoformat(task["early_finish_date"])
        except (KeyError,TypeError,ValueError) as exc:
            raise ValueError("baseline and forecast require valid ISO dates") from exc
        if planned_finish<planned_start:
            raise ValueError("baseline finish before start")
        rows.append({"id":tid,"baseline_status":"MATCHED",
                     "start_variance_days":(forecast_start-planned_start).days,
                     "finish_variance_days":(forecast_finish-planned_finish).days,
                     "critical":task["critical"]})
    for tid in indexed:
        if not any(row["id"]==tid for row in rows):
            rows.append({"id":tid,"baseline_status":"REMOVED","start_variance_days":None,"finish_variance_days":None})
    return {"baseline_id":baseline.get("id"),"baseline_approval_status":"APPROVED",
            "task_variances":rows,"delayed_task_ids":[r["id"] for r in rows if r["finish_variance_days"] is not None and r["finish_variance_days"]>0]}
