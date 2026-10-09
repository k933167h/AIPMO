# ADR-001: OpenProject + Plane integration baseline

Status: Proposed
Date: 2026-10-09
Branch: feature/openproject-plane-integration-m1

## Existing implementation
The current AIPMO app already includes FastAPI endpoints for weighted progress, EVM, CPM scheduling, GANTT-AX import/export, and approved baseline comparison. Preserve these modules and their existing API contracts.

## Ownership
- OpenProject: project plans, WBS, schedule and approved baseline source references.
- Plane: work items, cycles, modules and execution status.
- AIPMO: cross-system identity mapping, EVM calculations, policy, approvals, event journal, AI orchestration and audit evidence.
- Never write directly to OpenProject or Plane application databases.

## Integration contract
Adapters expose read_project, list_work_items, get_work_item and propose_change methods. Write operations require an explicit approval and idempotency key. The canonical mapping is scoped by tenant and project, with external_system, external_project_id, external_item_id and canonical_item_id. Do not assume one-to-one mapping: one WBS package may relate to many Plane items.

## Synchronization
Inbound webhook or polling -> verify source/authenticity -> durable inbox -> deduplicate -> normalize -> project -> reconcile. Maintain cursor and source revision. Never use last-write-wins for budget, baseline or contract changes. Handle retries and dead letters.

## Security
Store API tokens in a secret manager, never logs. Enforce least privilege, tenant isolation, allowlisted MCP tools, human approval for irreversible or high-impact writes. AI-generated instructions are untrusted; use deterministic policy validation before execution.

## Test gates
1. Contract tests for OpenProject API v3 and Plane REST response normalization, including pagination and errors.
2. Mapping tests: one-to-many links, duplicate webhooks, deleted items, cross-tenant rejection.
3. Integration tests against pinned self-hosted versions using disposable test credentials.
4. Regression tests for progress, EVM, CPM and approved baselines.
5. Negative tests for tool permissions, approval bypass, token leakage and prompt injection.
6. Generate CI evidence, update Architecture Overview and SPA Runbook before PR merge.

## Deployment
Keep official OpenProject and Plane compose stacks isolated; deploy AIPMO separately. Connect over authenticated APIs and dedicated network boundaries. Pin image digests, persist storage, test backup/restore, and verify license obligations for deployed versions.

## Next implementation slice
Implement read-only OpenProject and Plane adapters first, then canonical link storage, inbox events, and only then gated write actions. Confirm upstream API schema against the pinned versions before shipping.
