import pytest
from app.calendar import working_date,project_schedule_dates
from app.schedule import critical_path

def test_weekend_skipped():
    assert working_date("2026-10-09",1)=="2026-10-12"

def test_holiday_skipped():
    assert working_date("2026-10-09",1,["2026-10-12"])=="2026-10-13"

def test_start_weekend_rolls_forward():
    assert working_date("2026-10-10",0)=="2026-10-12"

def test_negative_offset():
    assert working_date("2026-10-12",-1)=="2026-10-09"

def test_schedule_projection():
    result=critical_path([{"id":"A","duration":1},{"id":"B","duration":2,"predecessors":["A"]}])
    dated=project_schedule_dates(result,"2026-10-09",["2026-10-12"])
    assert dated["project_finish_date"]=="2026-10-15"
    assert dated["tasks"][0]["early_finish_date"]=="2026-10-13"

def test_fractional_rejected():
    result=critical_path([{"id":"A","duration":0.5}])
    with pytest.raises(ValueError,match="integer"):
        project_schedule_dates(result,"2026-10-09")
