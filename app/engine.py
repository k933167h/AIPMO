from decimal import Decimal

def progress(tasks):
    if not tasks: return None
    weights = [Decimal(str(t["weight"])) for t in tasks]
    if any(w < 0 for w in weights) or sum(weights) == 0: raise ValueError("invalid weights")
    values = [Decimal(str(t["completion"])) for t in tasks]
    if any(v < 0 or v > 1 for v in values): raise ValueError("completion out of range")
    return float(100 * sum(w*v for w,v in zip(weights,values))/sum(weights))

def evm(pv,ev,ac,bac):
    pv,ev,ac,bac=map(lambda x: Decimal(str(x)),(pv,ev,ac,bac))
    if min(pv,ev,ac,bac)<0: raise ValueError("negative amounts")
    spi=ev/pv if pv else None
    cpi=ev/ac if ac else None
    eac=bac/cpi if cpi and cpi>0 else None
    def fmt(x): return float(x) if x is not None else None
    return {"sv":fmt(ev-pv),"cv":fmt(ev-ac),"spi":fmt(spi),"cpi":fmt(cpi),"eac":fmt(eac),"vac":fmt(bac-eac) if eac is not None else None}
