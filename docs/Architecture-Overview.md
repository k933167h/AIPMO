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


## v1.9 SME approval credential and audit
Approval endpoint now requires PMO_SME_APPROVAL_KEY via x-sme-key in addition to PMO_API_KEY. PostgreSQL stores PROPOSED and APPROVED audit events in the same transaction as baseline changes. GET /api/v1/baselines/{id}/audit returns events. This is a shared-role secret, not user-specific RBAC, immutable/WORM storage, or independently authenticated reviewer identity; these remain production requirements.


## v2.0 Identity-bound SME approval
PMO_IDENTITIES_JSON maps deployment-managed credentials to user_id and roles. SME approval and rejection require both shared SME key and x-identity-token for a user with SME role. Approval reviewer must match authenticated user_id. REJECTED is terminal and recorded in audit. Identity mapping is static deployment configuration, not enterprise SSO/OIDC; rejection reason is returned but not yet durably recorded in audit.


## v2.1 OIDC verification (opt-in)
Set PMO_AUTH_MODE=oidc, PMO_OIDC_ISSUER, PMO_OIDC_AUDIENCE and HTTPS PMO_OIDC_JWKS_URL to verify RS256 JWT signature, issuer, audience, expiration and SME role on approval/rejection. Legacy static identity mode remains default. JWKS network retrieval requires a reachable issuer; tests currently cover configuration failures only. Append-only audit cryptographic hash chaining and evidence storage remain pending.


## v2.2 Approval audit hash chain
New audit events record SHA-256 event_hash and prev_hash under PostgreSQL transaction-scoped advisory locking. GET /api/v1/baselines/{id}/audit/verify recomputes and validates links. Existing v1.9/v2.0 audit rows are not backfilled; schema migration must be applied for existing databases. Hash chaining alone does not prevent privileged database rewrites, deletions, or truncation; external signed/WORM checkpoints remain future work.

## v2.3 MCP PMO tool governance
AIPMO exposes a static allowlisted tool catalog and policy **simulation** API. No remote MCP tool is executed. The supplied roles and approval flags are untrusted and cannot be used as real execution authorization. Production enforcement requires verified identity, project scopes, server-side approvals, tool argument validation, per-resource OAuth, tracing and evidence.

## v2.4 GitHub snapshot normalization
POST /api/v1/integrations/github/snapshot accepts GitHub issue, pull request and workflow run data and normalizes it for PMO reporting. This endpoint does not retrieve remote data or execute MCP tools. Future work: authenticated GitHub read connector, paging, rate limits, evidence, WBS mapping.

## v2.5 GitHub REST read adapter and WBS references
GET /api/v1/integrations/github/{owner}/{repo}/sync fetches Issues, PRs and Actions workflow runs via read-only GitHub REST using PMO_GITHUB_READ_TOKEN. Pagination is bounded (default 2, maximum 5 pages per resource). WBS references are extracted from title tokens WBS-<id> or WBS:<id> and returned as proposed links, not authoritative schedule updates. No remote MCP transport, durable synchronization or automated story point inference yet. Token must be provisioned server-side with minimum read scopes; do not log or return it.

## v2.6 Multi-source WBS reconciliation
POST /api/v1/wbs/reconcile accepts Jira, Plane, GANTT-AX and GitHub link payloads, groups normalized work items by WBS ID, reports unmatched items and flags duplicate same-source references for review. This is a read-only reconciliation starter; it does not yet call Jira/Plane MCP servers, persist identity mappings or calculate trustworthy cross-tool story points. WBS labels require explicit source governance and SME confirmation before authoritative changes.

## v2.7 Jira and Plane read adapters
POST /api/v1/wbs/reconcile/remote reads Jira Cloud issues and Plane issues through HTTPS APIs using server-configured PMO_JIRA_URL, PMO_JIRA_EMAIL, PMO_JIRA_TOKEN, PMO_PLANE_URL and PMO_PLANE_TOKEN, then reconciles with GANTT-AX and GitHub links. API is read-only, has a 10-second request timeout and retrieves up to 100 records per provider (first page only). No actual MCP protocol transport, pagination beyond first page, project-scoped authorization, or production credentialed integration test is implemented. Deploy behind project authorization and least-privilege credentials before operational use.

## v2.8 Bounded pagination
POST /api/v1/wbs/reconcile/paged retrieves up to five pages of 100 Jira and Plane issues each, then reconciles against supplied GANTT-AX/GitHub WBS references. The max_pages parameter defaults to 3. Jira uses startAt and total; Plane uses page/per_page. This is bounded bulk reading, NOT incremental synchronization: cursor/watermark persistence, rate-limit retry, multi-tenant authorization and complete provider-specific pagination validation are future work.

## v2.9 Project scope and delta-filtering foundation
POST /api/v1/wbs/changes requires PMO_API_KEY and checks both Jira project key and Plane project ID against PMO_ALLOWED_PROJECTS (comma-separated, fail closed). It retrieves bounded pages and filters returned records by updated timestamp, reporting missing timestamps separately. This is client-side delta filtering, not provider-side incremental fetching or persistent checkpointing. It cannot guarantee a complete change feed, particularly when changed items exceed page limits. Multi-tenant identity authorization and external credentialed tests remain pending.

## v3.0 PostgreSQL sync run and checkpoint persistence
pmo_sync_runs stores immutable run outcomes and observed counts; pmo_sync_checkpoints stores provider/project watermarks and advances them only on successful explicit record_sync calls. POST /api/v1/sync/runs and GET /api/v1/sync/checkpoints/{provider}/{project_key} require PMO_API_KEY and project allowlisting. This milestone is a checkpoint persistence primitive: it does not automatically execute or validate remote synchronization, guarantee complete pages, or authorize arbitrary callers to claim successful runs. In production the write endpoint must be restricted to a trusted synchronization worker, and checkpoint commits must be coupled to durable ingestion.

## v3.1 Explicit synchronization worker
POST /api/v1/sync/execute requires PMO_API_KEY, a distinct PMO_SYNC_WORKER_KEY header, and PMO_ALLOWED_PROJECTS. A worker reads bounded Jira/Plane pages, validates all timestamps, and atomically upserts JSONB work items, successful run history and monotonic checkpoints in one PostgreSQL transaction. Reaching the configured page cap fails closed without persisting a success checkpoint. This is a manually triggered bulk synchronization primitive, not provider-native incremental API fetching, scheduler, webhook consumer or guaranteed complete ingestion. The legacy /api/v1/sync/runs route remains a separate trust risk until restricted or removed.
