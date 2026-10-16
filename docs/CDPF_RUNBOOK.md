# CDPF v1.1 integration runbook
## Architecture
AIPMO / Plane / Kiwi / Langfuse snapshots -> normalize -> canonical signals -> weighted risk score -> PMO review.
No external API polling or durable persistence is included in this iteration.
## Deployment
Use the existing AIPMO Docker image and API key configuration. The CDPF router is mounted in app/main.py.
## Test
Run `pytest -q tests/test_cdpf.py` and then `pytest -q`.
## API
POST /api/v1/cdpf/normalize with X-API-Key:
`{"project_id":"P1","source":"plane","records":[{"id":"ISSUE-17","event_type":"reopened_issue","severity":85,"observed_at":"2026-10-16T09:00:00Z"}]}`
POST /api/v1/cdpf/evaluate with X-API-Key and returned signals.
## Safety and limitations
Missing dimensions yield coverage < 1 and must not be interpreted as zero risk.
Never send credentials or private customer messages in event payloads.
Before production add cursor polling, rate limits, idempotent persistent ingestion, RBAC, audit, retention and manual escalation approval.
