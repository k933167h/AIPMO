import pytest
from app.schedule import critical_path
from app.calendar import project_schedule_dates
from app.baseline import compare_baseline

def fixture():
    return project_schedule_dates(critical_path([{"id":"A","duration":2}]),"2026-10-09")

def test_approved_baseline_delay():
    baseline={"id":"BL-1","approval_status":"APPROVED","tasks":[{"id":"A","start_date":"2026-10-08","finish_date":"2026-10-12"}]}
    result=compare_baseline(fixture(),baseline)
    assert result["delayed_task_ids"]==["A"]
    assert result["task_variances"][0]["finish_variance_days"]==1

def test_unapproved_baseline_rejected():
    with pytest.raises(ValueError,match="approved"):
        compare_baseline(fixture(),{"approval_status":"STAGED","tasks":[]})

def test_new_removed_tasks():
    baseline={"approval_status":"APPROVED","tasks":[{"id":"B","start_date":"2026-10-09","finish_date":"2026-10-12"}]}
    result=compare_baseline(fixture(),baseline)
    assert [r["baseline_status"] for r in result["task_variances"]]==["NEW","REMOVED"]

def test_invalid_baseline_date():
    baseline={"approval_status":"APPROVED","tasks":[{"id":"A","start_date":"bad","finish_date":"2026-10-12"}]}
    with pytest.raises(ValueError,match="valid ISO"):
        compare_baseline(fixture(),baseline)
