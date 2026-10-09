import uuid
import pytest
from app import artifact_store as store
from app.artifact_registry import stable_id

def test_register_and_list_postgres():
    project="artifact-"+uuid.uuid4().hex[:12]
    wbs="WBS-01"
    item=store.register(project,wbs,"wiki","docmost","page-7",
                        "https://wiki.internal/pages/7",{"title":"Design"})
    assert item["reference_id"]==stable_id(project,wbs,"wiki","docmost","page-7")
    store.register(project,wbs,"wiki","docmost","page-7",
                   "https://wiki.internal/pages/7",{"title":"Updated"})
    links=store.list_links(project,wbs)
    assert len(links)==1
    assert links[0]["metadata"]["title"]=="Updated"
    assert store.list_links(project,"WBS-02")==[]

def test_invalid_artifact_url():
    with pytest.raises(ValueError):
        store.register("P","W","file","nextcloud","1","http://external.example")
