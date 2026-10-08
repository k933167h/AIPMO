# AIPMO Architecture v1.4

GANTT-AX v7.3 project JSON → authenticated FastAPI import → validation/normalization → PostgreSQL JSONB STAGED snapshot → authenticated original JSON export.

Deterministic progress/EVM and new DAG-based CPM schedule API (/api/v1/schedule/cpm). CPM currently supports FS zero-lag dependencies with elapsed-day durations; not yet full GANTT-AX working-calendar semantics.

CI covers unit, API and disposable PostgreSQL integration tests. Source imports never become approved baselines automatically.

Planned: full dependency types, calendars, Excel mapping, MCP GitHub/Plane, RBAC, approvals, AX QE OS and SPA.


## v1.5 dependency extension
CPM supports FS, SS, FF and SF dependencies with signed elapsed-day lag. Legacy predecessor strings remain FS with zero lag. Workday calendars and holidays are not yet supported.
