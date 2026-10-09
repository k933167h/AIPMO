"""Compare Nextcloud WebDAV snapshots using stable metadata fingerprints."""
import hashlib
import json

def fingerprint(item):
    keys=("href","etag","modified","size")
    if not item.get("href"): raise ValueError("missing resource href")
    data={k:item.get(k) for k in keys}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

def diff_snapshots(previous,current):
    old={item["href"]:fingerprint(item) for item in previous}
    new={item["href"]:fingerprint(item) for item in current}
    return {"changed":sorted(k for k in new if old.get(k)!=new[k]),
            "deleted":sorted(k for k in old if k not in new),
            "unchanged":sum(old.get(k)==v for k,v in new.items())}
