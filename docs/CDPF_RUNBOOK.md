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

## Persistent ingestion
POST /api/v1/cdpf/ingest with the same JSON body as normalize, and X-API-Key.
GET /api/v1/cdpf/projects/{project_id}/risk with X-API-Key.
PostgreSQL uses DATABASE_URL already configured by AIPMO. Table cdpf_evidence is created lazily.
Primary key (project_id,source,source_id) ensures idempotent upsert; older observations cannot overwrite newer ones.
The API key grants global access to project risk data; project-scoped RBAC is required before multi-tenant production use.
No automated external polling is implemented yet.
## Verification
Run pytest -q tests/test_cdpf.py tests/test_cdpf_persistence_api.py
Run full pytest -q and inspect GitHub Actions before merge.
Use a staging PostgreSQL service to test real SQL DDL, conflict handling, persistence across restart, and database permissions.
