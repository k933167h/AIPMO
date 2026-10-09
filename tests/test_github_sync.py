from app.github_sync import normalize_issues,normalize_pull_requests,normalize_workflow_runs,project_snapshot

def test_issue_filter_and_labels():
    items=[{"number":1,"title":"Implement WBS","state":"open","labels":[{"name":"schedule"}]},
           {"number":2,"pull_request":{"url":"example"},"state":"open"}]
    issues=normalize_issues(items)
    assert len(issues)==1
    assert issues[0]["labels"]==["schedule"]

def test_pr_and_ci_summary():
    snapshot=project_snapshot(
        [{"number":1,"state":"open"}],
        [{"number":3,"state":"open","draft":True}],
        [{"id":99,"status":"completed","conclusion":"failure","head_sha":"abc"}])
    assert snapshot["summary"]=={"open_issues":1,"open_prs":1,"failed_ci_runs":1}
    assert snapshot["workflow_runs"][0]["head_sha"]=="abc"

def test_bad_timestamp_is_safe():
    result=normalize_workflow_runs([{"id":1,"updated_at":"not-a-date"}])
    assert result[0]["updated_at"] is None
