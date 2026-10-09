import httpx
import pytest
from app.github_collector import collect_github

class FakeClient:
    def get(self,url,**kwargs):
        if url.endswith("/issues"):
            return httpx.Response(200,json=[
                {"number":1,"title":"Fix task","state":"open","html_url":"https://github.com/o/r/issues/1","labels":[{"name":"bug"}]},
                {"number":2,"title":"PR issue shadow","pull_request":{},"state":"open"}],
                request=httpx.Request("GET",url))
        return httpx.Response(200,json=[{"number":2,"title":"Feature","state":"open","html_url":"https://github.com/o/r/pull/2","merged_at":None}],
                              request=httpx.Request("GET",url))

def test_normalize_issues_and_prs():
    result=collect_github("o/r",token="test",client=FakeClient())
    assert result["counts"]=={"issues":1,"pull_requests":1}
    assert result["issues"][0]["labels"]==["bug"]
    assert result["partial"] is False

def test_reject_invalid_repo():
    with pytest.raises(ValueError): collect_github("../unsafe",token="test",client=FakeClient())
