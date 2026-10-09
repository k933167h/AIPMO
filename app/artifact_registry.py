"""Provider-independent WBS artifact references."""
import hashlib
import json

KINDS = {"wiki", "file", "message", "test", "defect", "task"}

def stable_id(project,wbs,kind,source,external_id):
    if kind not in KINDS or not all((project,wbs,source,external_id)):
        raise ValueError('invalid artifact reference')
    data=json.dumps([project,wbs,kind,source,external_id],ensure_ascii=False)
    return hashlib.sha256(data.encode()).hexdigest()
