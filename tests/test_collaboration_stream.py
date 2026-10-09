from app.nextcloud_delta import diff_snapshots
from app import collaboration_stream as stream

def test_diff():
    assert diff_snapshots([{'href':'/a','etag':'1'}],[{'href':'/a','etag':'2'}])['changed']==['/a']

def test_chunks(monkeypatch):
    commits=[]
    monkeypatch.setattr(stream,'apply_batch',lambda *args: commits.append(args))
    stream.commit_message_chunks('P','stream-1',[{'id':1,'wbs_ids':['WBS-1']},{'id':2,'wbs_ids':['WBS-1']}],chunk_size=1)
    assert len(commits)==2
