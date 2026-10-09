import pytest
from app.integration_algorithms import rollup_progress, schedule_risk


def test_weighted_progress_and_shared_item():
    result = rollup_progress(
        [{"id": "A", "weight": 3, "completion": 0},
         {"id": "B", "weight": 1, "completion": 1}],
        [{"id": "P1", "completion": 0.5}],
        [{"package_id": "A", "item_id": "P1", "allocation": 0.5},
         {"package_id": "B", "item_id": "P1", "allocation": 0.5}])
    assert result["progress_pct"] == 50
    assert result["package_completion"] == {"A": 0.5, "B": 0.5}


@pytest.mark.parametrize("links", [
    [{"package_id": "A", "item_id": "X", "allocation": 0.8},
     {"package_id": "B", "item_id": "X", "allocation": 0.8}],
    [{"package_id": "A", "item_id": "X", "allocation": 1},
     {"package_id": "A", "item_id": "X", "allocation": 1}],
])
def test_reject_double_count(links):
    with pytest.raises(ValueError):
        rollup_progress(
            [{"id": "A", "weight": 1, "completion": 0},
             {"id": "B", "weight": 1, "completion": 0}],
            [{"id": "X", "completion": 0.5}], links)


def test_unmapped_package_preserves_manual_completion():
    assert rollup_progress([{"id": "A", "weight": 1, "completion": 0.25}], [], [])["progress_pct"] == 25


def test_schedule_risk():
    result = schedule_risk([{"id": "A", "due_date": "2026-10-01", "completion": 0.5},
                            {"id": "B", "due_date": "2026-10-10", "completion": 1}], "2026-10-09")
    assert result == [{"id": "A", "kind": "overdue", "days": 8}]
