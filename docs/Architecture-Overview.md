# AIPMO Architecture v1.3

GANTT-AX v7.3 project JSON → authenticated FastAPI import → validation/normalization → PostgreSQL JSONB STAGED snapshot → authenticated original JSON export.

Deterministic progress and EVM endpoints remain. Imported data never automatically becomes an approved baseline.

## Validation
CI executes unit tests, authenticated API tests, and a real PostgreSQL roundtrip against a disposable GitHub Actions service database. Review actual CI status before merging.

## Planned
Full source JSON compatibility; Excel mapping; migration framework; MCP GitHub/Plane; RBAC and approval; AX QE OS; SPA.
