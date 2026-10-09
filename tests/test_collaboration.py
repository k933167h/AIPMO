import pytest
from app import collaboration as c

def test_unsafe_service_urls():
    for url in ("http://localhost:8000","https://user:pass@host","https://host?next=evil"):
        with pytest.raises(ValueError): c._base(url)

def test_zulip_channels(monkeypatch):
    monkeypatch.setenv("PMO_ZULIP_URL","https://zulip.internal")
    monkeypatch.setenv("PMO_ZULIP_EMAIL","bot@example.internal")
    monkeypatch.setenv("PMO_ZULIP_API_KEY","test")
    monkeypatch.setattr(c,"_json_get",lambda base,path,headers:{"result":"success","streams":[{"stream_id":7,"name":"WBS"}]})
    assert c.zulip_channels()==[{"id":7,"name":"WBS"}]

def test_nextcloud_capabilities(monkeypatch):
    monkeypatch.setenv("PMO_NEXTCLOUD_URL","https://cloud.internal")
    monkeypatch.setenv("PMO_NEXTCLOUD_USER","bot")
    monkeypatch.setenv("PMO_NEXTCLOUD_APP_PASSWORD","test")
    monkeypatch.setattr(c,"_json_get",lambda base,path,headers:{"ocs":{"data":{"capabilities":{"files":{}}}}})
    assert "files" in c.nextcloud_capabilities()

def test_docmost_license_boundary(monkeypatch):
    monkeypatch.setenv("PMO_DOCMOST_URL","https://wiki.internal")
    assert c.docmost_integration_status()["mode"]=="manual_link_only"
