from app.collaboration_mapping import detect_wbs,artifact_candidates
from app import collaboration_ingest as ingest

def test_wbs_detection_deduplicates():
    assert detect_wbs("APGW-01 and WBS-42; APGW-01")==["APGW-01","WBS-42"]

def test_unmatched_not_registered():
    assert artifact_candidates("P","wiki","docmost","1","general notes")==[]

def test_zulip_ingest(monkeypatch):
    monkeypatch.setattr(ingest,"check_project_access",lambda project: True)
    monkeypatch.setattr(ingest,"zulip_recent_messages",lambda stream:[{"id":42,"subject":"APGW-01 Design"}])
    monkeypatch.setattr(ingest,"register",lambda *args,**kwargs:{"reference_id":"ref"})
    assert ingest.ingest_zulip("P",7)["registered"]==1

def test_nextcloud_ingest(monkeypatch):
    monkeypatch.setattr(ingest,"check_project_access",lambda project: True)
    monkeypatch.setattr(ingest,"nextcloud_list_folder",lambda folder:[{"href":"/dav/WBS-42_plan.pdf"}])
    monkeypatch.setattr(ingest,"register",lambda *args,**kwargs:{"reference_id":"ref"})
    assert ingest.ingest_nextcloud("P")["registered"]==1
