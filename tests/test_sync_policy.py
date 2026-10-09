from app.sync_policy import check_project_access, changed_since


def test_project_scope():
    assert check_project_access('P', 'P,Q') is True


def test_delta():
    data = [{'updated': '2026-10-09T00:00:00Z'}]
    assert len(changed_since(data, '2026-10-08T00:00:00Z')['changed']) == 1
