# GANTT-AX v7.3 → AIPMO Integration Assessment

## Source
Uploaded standalone HTML, SHA-256: `695a084bbb3b10f8f74e559d7a4beb578725fd261fa563aabab2d958dfbeba41`.
The HTML is a reference application, **not** a real project dataset. Do not treat seeded demo tasks as actual project status.

## Confirmed functional areas
- WBS / Gantt / dependencies / critical path; Baseline, Actual, Forecast
- EVM, progress, FP, VBS
- Resource workload, leveling, skill pool/gap
- CCPM buffers, Monte Carlo
- RAID, governance, action workflow, approval/RACI
- Portfolio, procurement, vendor, financial forecast
- AX Engineering, AI Evaluation, Quality, Runtime Trace, Evidence Graph, Assurance Gates
- Responsive SPA, JSON/localStorage project state, Excel transformation

## Source state model
`freshState()` creates `project`, `tasks`, `holidays`, `weekendDays`, `fp`, `baseline`, `vbs`, `resources`, `governance`, `ccpm`, `monteCarlo`, `ax`, `quality`, `portfolio`, `pmo`, `portfolioPlanning`, `gateReadiness`, `assurance`, `aiEvaluation`, `runtime`, `continuousAssurance`.
Browser localStorage key: `gantt_ax_project_v1`.

## Integration strategy
1. Preserve original HTML as reference, not an authoritative server application.
2. Introduce read-only import adapter for project/tasks, validating IDs, dates, dependencies and progress.
3. Store imported snapshots with source hash, import ID, timestamp, and mapping version. Require PM confirmation before replacing project baseline.
4. Add bidirectional mapping only after versioned persistence, RBAC, approval and audit are implemented.
5. Use deterministic server calculations for CPM/EVM and cross-check against browser formulas using Golden fixtures.
6. Surface the source feature groups in the AIPMO SPA incrementally; do not assume all are implemented in the starter.

## Next gates
- Add authenticated upload API and PostgreSQL staging tables.
- Build source/export compatibility tests with representative real project JSON.
- Validate Excel formula and date semantics, holidays, workday calendars, dependency lag.
- Gate write-back to GitHub/Plane behind explicit approval.
