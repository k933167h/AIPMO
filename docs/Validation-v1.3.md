# AIPMO v1.3 Validation Plan

## Scope
- API authorization, invalid JSON validation, roundtrip with mocked persistence
- Real PostgreSQL roundtrip with a disposable CI service database
- Source SHA-256 provenance and STAGED status
- Python module import discovery via python -m pytest

## Evidence
GitHub Actions job logs are the evidence source. CI success is not asserted until checked.

## Known limitations
No actual user project JSON uploaded; attached HTML is the application implementation.
The test fixture is synthetic. It does not validate every GANTT-AX v7.3 export variation.
Production multi-tenancy, RBAC, import size limits, migrations and approval workflows remain pending.
