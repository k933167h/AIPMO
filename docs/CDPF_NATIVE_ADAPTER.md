# CDPF native mapping and incremental checkpoints
Native translation helpers are provided for Plane work items, Kiwi test executions, and Langfuse quality scores.
These are schema-specific mappers, not live API clients. Confirm deployed API field names and pagination.
Use app.cdpf.incremental.get_cursor(project,source) to load a cursor and checkpoint(project,source,signals,cursor) to atomically store evidence and cursor.
The caller MUST only checkpoint a cursor after all pages up to that cursor have been fetched and validated.
Never pass arbitrary URLs or cursor URLs from an API to the polling client; use allowlisted HTTPS endpoints.
Production readiness requires integration tests against deployed Plane, Kiwi, Langfuse, and PostgreSQL; add per-source authentication, backoff, pagination, scheduling, and project-level RBAC.
