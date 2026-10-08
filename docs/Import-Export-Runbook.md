# GANTT-AX JSON Import/Export — AIPMO v1.2

1. Start PostgreSQL and API with `docker compose up --build`.
2. Configure `PMO_API_KEY` in a private .env file.
3. POST a JSON project state to `/api/v1/ganttax/imports` with `X-API-Key`.
4. The response returns import ID, source SHA-256, task count and STAGED status.
5. GET `/api/v1/ganttax/imports/{import_id}/export` retrieves the original JSON state.
6. Imported state is **never** automatically promoted to approved project baseline.
7. Confirm mapping, calendar, dependencies, weights and source version with the PM before using for schedule/budget decisions.

Limitations: JSON-only, no Excel import, no automatic source synchronization, no write-back to GitHub or Plane, no production-ready IAM. This is a development starter.
