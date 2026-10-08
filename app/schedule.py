"""CPM with FS/SS/FF/SF constraints and signed lag (elapsed-day units)."""
from collections import deque
import math

def critical_path(tasks):
    if not tasks:
        return {"project_duration_days":0,"tasks":[],"critical_task_ids":[]}
    nodes={}
    for task in tasks:
        tid=task["id"]
        duration=float(task["duration"])
        if not isinstance(tid,str) or not tid or tid in nodes or not math.isfinite(duration) or duration<0:
            raise ValueError("invalid task id or duration")
        nodes[tid]={"duration":duration,"predecessors":list(task.get("predecessors",[]))}
    successors={tid:[] for tid in nodes}
    indegree={tid:0 for tid in nodes}
    edges=[]
    for tid,node in nodes.items():
        seen=set()
        for predecessor in node["predecessors"]:
            if isinstance(predecessor,str):
                pid,kind,lag=predecessor,"FS",0.0
            elif isinstance(predecessor,dict):
                pid=predecessor.get("id")
                kind=predecessor.get("type","FS")
                try: lag=float(predecessor.get("lag",0))
                except (TypeError,ValueError): raise ValueError("invalid lag")
            else:
                raise ValueError("invalid predecessor")
            if not isinstance(pid,str) or pid not in nodes or pid==tid:
                raise ValueError("missing or self predecessor")
            if kind not in ("FS","SS","FF","SF") or not math.isfinite(lag):
                raise ValueError("invalid dependency type or lag")
            if (pid,kind) in seen:
                raise ValueError("duplicate predecessor")
            seen.add((pid,kind))
            # Constraint start(successor) >= start(predecessor) + offset.
            pd=nodes[pid]["duration"]
            sd=node["duration"]
            offset={"FS":pd,"SS":0,"FF":pd-sd,"SF":-sd}[kind]+lag
            edges.append((pid,tid,offset))
            successors[pid].append((tid,offset))
            indegree[tid]+=1
    queue=deque(tid for tid,degree in indegree.items() if degree==0)
    order=[]
    while queue:
        tid=queue.popleft()
        order.append(tid)
        for child,_ in successors[tid]:
            indegree[child]-=1
            if indegree[child]==0: queue.append(child)
    if len(order)!=len(nodes):
        raise ValueError("cyclic dependencies")
    es={tid:0.0 for tid in nodes}
    for tid in order:
        for child,offset in successors[tid]:
            es[child]=max(es[child],es[tid]+offset)
    ef={tid:es[tid]+nodes[tid]["duration"] for tid in nodes}
    finish=max(ef.values())
    ls={tid:finish-nodes[tid]["duration"] for tid in nodes}
    for tid in reversed(order):
        for child,offset in successors[tid]:
            ls[tid]=min(ls[tid],ls[child]-offset)
    rows=[]
    for tid in order:
        duration=nodes[tid]["duration"]
        total_float=round(ls[tid]-es[tid],9)
        rows.append({"id":tid,"early_start":es[tid],"early_finish":ef[tid],
                     "late_start":ls[tid],"late_finish":ls[tid]+duration,
                     "total_float":total_float,"critical":abs(total_float)<1e-9})
    return {"project_duration_days":finish,"tasks":rows,
            "critical_task_ids":[row["id"] for row in rows if row["critical"]]}
