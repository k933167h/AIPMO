from app.wbs_reconcile import reconcile_wbs

def test_multisource_wbs_join():
    result=reconcile_wbs(
      [{"key":"PM-1","fields":{"summary":"WBS-APGW-01 gateway","status":{"name":"In Progress"}}}],
      [{"id":"plane-1","name":"WBS:APGW-01 implementation","state":"started"}],
      [{"id":"APGW-01","name":"API Gateway"}],
      [{"wbs_id":"APGW-01","external_id":"github:issue:10"}])
    assert result["total_records"]==4
    assert len(result["work_items"])==1
    assert result["work_items"][0]["source_count"]==4
    assert result["work_items"][0]["needs_review"] is False

def test_missing_wbs_unmatched():
    result=reconcile_wbs([{"key":"PM-2","fields":{"summary":"No identifier"}}],[],[])
    assert len(result["unmatched"])==1

def test_duplicate_source_requires_review():
    result=reconcile_wbs([{"key":"PM-1","fields":{"summary":"WBS-T1"}},
                          {"key":"PM-2","fields":{"summary":"WBS-T1"}}],[],[])
    assert result["work_items"][0]["needs_review"] is True
