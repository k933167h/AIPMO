# AIPMO Architecture v1.4

GANTT-AX v7.3 project JSON → authenticated FastAPI import → validation/normalization → PostgreSQL JSONB STAGED snapshot → authenticated original JSON export.

Deterministic progress/EVM and new DAG-based CPM schedule API (/api/v1/schedule/cpm). CPM currently supports FS zero-lag dependencies with elapsed-day durations; not yet full GANTT-AX working-calendar semantics.

CI covers unit, API and disposable PostgreSQL integration tests. Source imports never become approved baselines automatically.

Planned: full dependency types, calendars, Excel mapping, MCP GitHub/Plane, RBAC, approvals, AX QE OS and SPA.


## v1.5 dependency extension
CPM supports FS, SS, FF and SF dependencies with signed elapsed-day lag. Legacy predecessor strings remain FS with zero lag. Workday calendars and holidays are not yet supported.


## v1.6 Workday calendar projection
Optional project_start, holidays and working_weekdays add working-date boundaries to integer-unit CPM output. This is a date projection of elapsed-day CPM, not a full working-time constraint solver; noninteger boundaries are rejected. Holidays are supplied by caller.


## v1.7 Baseline variance
Optional approved baseline comparison in /api/v1/schedule/cpm requires project_start. Returns calendar-day start/finish variance, delayed tasks and added/removed tasks. Approval status is supplied by the caller and not independently verified against an approval store.


## v1.8 baseline approval
PostgreSQL stores baseline proposals as STAGED JSONB records. A separate endpoint transitions them to APPROVED once. CPM can load an approved baseline by baseline_id. Reviewer identity is currently caller-supplied and not independently authenticated; tenant RBAC and immutable audit history remain future work.
