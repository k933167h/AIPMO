"""Deterministic CPM schedule for a validated directed acyclic WBS network."""
from collections import deque

def critical_path(tasks):
    if not tasks:
        return {"project_duration_days": 0, "tasks": [], "critical_task_ids": []}
    by_id = {}
    for task in tasks:
        tid = task["id"]
        duration = float(task["duration"])
        if not isinstance(tid,str) or not tid or tid in by_id or duration < 0:
            raise ValueError("invalid task id or duration")
        by_id[tid] = {"id":tid, "duration":duration, "predecessors":list(task.get("predecessors",[]))}
    indegree = {tid:0 for tid in by_id}
    successors = {tid:[] for tid in by_id}
    for tid,t in by_id.items():
        for p in t["predecessors"]:
            if p not in by_id or p == tid:
                raise ValueError("missing or self predecessor")
            if tid in successors[p]:
                raise ValueError("duplicate predecessor")
            successors[p].append(tid)
            indegree[tid] += 1
    queue = deque(tid for tid,n in indegree.items() if n==0)
    order=[]
    while queue:
        tid=queue.popleft()
        order.append(tid)
        for child in successors[tid]:
            indegree[child]-=1
            if indegree[child]==0:
                queue.append(child)
    if len(order)!=len(by_id):
        raise ValueError("cyclic dependencies")
    es,ef={},{}
    for tid in order:
        es[tid]=max((ef[p] for p in by_id[tid]["predecessors"]),default=0)
        ef[tid]=es[tid]+by_id[tid]["duration"]
    finish=max(ef.values())
    ls,lf={},{}
    for tid in reversed(order):
        lf[tid]=min((ls[s] for s in successors[tid]),default=finish)
        ls[tid]=lf[tid]-by_id[tid]["duration"]
    rows=[{"id":tid,"early_start":es[tid],"early_finish":ef[tid],"late_start":ls[tid],"late_finish":lf[tid],"total_float":round(ls[tid]-es[tid],9),"critical":abs(ls[tid]-es[tid])<1e-9} for tid in order]
    return {"project_duration_days":finish,"tasks":rows,"critical_task_ids":[t["id"] for t in rows if t["critical"]]}
