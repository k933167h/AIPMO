"""Workday calendar utilities for CPM milestone date projection."""
from datetime import date, timedelta

def _date(value):
    return date.fromisoformat(value) if isinstance(value,str) else value

def working_date(start, offset, holidays=(), weekdays=(0,1,2,3,4)):
    """Project an integer working-day offset from start (offset 0 = first working date)."""
    current=_date(start)
    closed={_date(value) for value in holidays}
    open_days=set(weekdays)
    if not open_days or any(not isinstance(day,int) or day<0 or day>6 for day in open_days):
        raise ValueError("invalid working weekdays")
    if not isinstance(offset,int):
        raise ValueError("working-day offset must be integer")
    if current.weekday() not in open_days or current in closed:
        while current.weekday() not in open_days or current in closed:
            current+=timedelta(days=1)
    step=1 if offset>=0 else -1
    for _ in range(abs(offset)):
        current+=timedelta(days=step)
        while current.weekday() not in open_days or current in closed:
            current+=timedelta(days=step)
    return current.isoformat()

def project_schedule_dates(result, start, holidays=(), weekdays=(0,1,2,3,4)):
    """Annotate integer-unit CPM schedule with working-date boundaries.

    Duration and lag must be whole working days. Boundary dates represent start
    and finish boundaries; a 1-day task starting Monday finishes Tuesday.
    """
    rows=[]
    for row in result["tasks"]:
        boundaries={}
        for key in ("early_start","early_finish","late_start","late_finish"):
            value=row[key]
            if int(value)!=value:
                raise ValueError("calendar projection requires integer CPM boundaries")
            boundaries[key+"_date"]=working_date(start,int(value),holidays,weekdays)
        rows.append({**row,**boundaries})
    duration=result["project_duration_days"]
    if int(duration)!=duration:
        raise ValueError("calendar projection requires integer CPM duration")
    return {**result,"tasks":rows,"project_finish_date":working_date(start,int(duration),holidays,weekdays)}
