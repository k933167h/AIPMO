# CPM v1.4

Deterministic directed acyclic graph CPM (forward/backward pass). Durations are abstract elapsed-day units, not business-calendar days. Supports finish-to-start zero-lag dependencies only. Calculates ES, EF, LS, LF, float and critical tasks. Rejects cycles, missing predecessors and duplicate edges.

GANTT-AX v7.3 supports richer dependencies, holidays, calendars and resource constraints. This module does **not** yet claim parity. Future: FS/SS/FF/SF lag, working calendars, baseline and resource leveling.
