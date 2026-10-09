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

## v2.3 MCP Project Management Governance (starter)
Reference architecture: PMO Agents → policy enforcement gateway → allowlisted MCP connectors (GitHub, Jira/Plane, Kiwi/AX QE OS, document stores, observability) → normalized PMO data / evidence. First milestone implements a **static tool catalog and pure policy evaluation**, not an MCP server, remote tool execution, OAuth exchange or an enforceable authorization boundary. GET /api/v1/mcp/tools lists allowed tool definitions. POST /api/v1/mcp/policy/check is a **simulation only**: caller-supplied roles and approved values are untrusted and must never authorize real tool execution. Real enforcement must derive roles from verified OIDC claims and approvals from persisted SME decisions, check project scope and tool arguments, log invocation IDs, redact secrets, and verify resource-scoped OAuth access tokens. High-risk write/merge/deploy operations require human confirmation, least-privilege scopes and audit evidence. Recommended stages: GitHub read-only → Jira/Plane WBS sync → CPM/EVM reconciliation → Kiwi quality gates → guarded write actions → graph-based traceability. Protocol interoperability and security baselines should track modelcontextprotocol.io specifications and official provider guidance.
