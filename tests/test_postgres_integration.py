"""Run with DATABASE_URL pointing to a disposable PostgreSQL database."""
import os
import pytest
from app.store import stage_import, export_import

@pytest.mark.integration
def test_postgres_roundtrip():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not configured")
    source={"project":{"code":"IT-TEST","name":"Integration"},"tasks":[{"id":"T1","name":"Task","progress":25,"duration":3}],"holidays":["2026-10-09"]}
    created=stage_import(source)
    assert created["status"]=="STAGED"
    assert len(created["source_sha256"])==64
    assert export_import(created["import_id"])==source
