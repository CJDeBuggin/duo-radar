import json, random, time, datetime, requests, os
PART="MK1E4LL/A"; ZIP="63117"
STORES={"R114":"Apple Saint Louis Galleria","R062":"Apple West County"}
MODELS={"MK1E4LL/A":"256GB Star White","MK1F4LL/A":"256GB Night Sky","MK1G4LL/A":"512GB Star White","MK1H4LL/A":"512GB Night Sky","MK1J4LL/A":"1TB Star White","MK1L4LL/A":"1TB Night Sky","MK1Q4LL/A":"2TB Star White","MK1R4LL/A":"2TB Night Sky"}
URL="https://www.apple.com/shop/retail/pickup-message?"+"&".join(f"parts.{i}={p}" for i,p in enumerate(MODELS))+f"&location={ZIP}"
lastm={(p,k):False for p in MODELS for k in STORES}; curm=dict(lastm)
BUY="https://www.apple.com/shop/buy-iphone/iphone-duo/7.6-inch-display-256gb-star-white"
ALERTS={"MK1E4LL/A":("Star White",BUY),"MK1F4LL/A":("Night Sky","https://www.apple.com/shop/buy-iphone/iphone-duo/7.6-inch-display-256gb-night-sky")}
lasta={(p,k):False for p in ALERTS for k in STORES}
TOPIC=open(os.path.join(os.path.dirname(__file__),"topic.txt")).read().strip()
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
STATUS=os.path.join(os.path.dirname(__file__),"status.json")
SITE=os.path.join(os.path.dirname(__file__),"site","status.json")
HIST=os.path.join(os.path.dirname(__file__),"history.json")
try: history=json.load(open(HIST))
except Exception: history=[]
ROLEF=os.path.join(os.path.dirname(__file__),"role.txt")
ROLE=open(ROLEF).read().strip() if os.path.exists(ROLEF) else "primary"
SRC="pc" if ROLE=="primary" else "box"
STARTED=datetime.datetime.now().isoformat(timespec="seconds")
last_ok=None
def site_write(ok,cur,err=None):
    av=[p for p in ALERTS if any(curm.get((p,k)) for k in STORES)]
    d={"now":datetime.datetime.now().isoformat(timespec="seconds"),"ok":ok,"last_ok":last_ok,"started":STARTED,"checks":checks,
       "product":"iPhone Duo 256GB Star White or Night Sky","src":SRC,"buy":ALERTS[av[0]][1] if av else BUY,"error":err,
       "alerts":[MODELS[p] for p in ALERTS],
       "stores":[{"id":k,"name":v,"available":bool(cur.get(k)),"models":[MODELS[p] for p in ALERTS if curm.get((p,k))]} for k,v in STORES.items()],"history":history[-25:],
       "models":[{"m":MODELS[p],"a":[1 if curm.get((p,k)) else 0 for k in STORES]} for p in MODELS]}
    tmp=SITE+".tmp"; json.dump(d,open(tmp,"w")); os.replace(tmp,SITE); pub_status(d)
STOPIC=open(os.path.join(os.path.dirname(__file__),"status_topic.txt")).read().strip()
_lastpub=[0,None]
STATSF=os.path.join(os.path.dirname(__file__),"stats.json")
try: stats=json.load(open(STATSF))
except Exception: stats={}
def stat(ok,ms=0):
    k=datetime.datetime.now().strftime("%Y-%m-%dT%H"); s=stats.setdefault(k,[0,0,0])
    if ok: s[0]+=1; s[2]+=int(ms)
    else: s[1]+=1
    for old in sorted(stats)[:-72]: stats.pop(old)
    json.dump(stats,open(STATSF,"w"))
def pub_status(d):
    key=(datetime.datetime.now().hour,d["ok"],tuple(x["available"] for x in d["stores"]),len(d["history"]),json.dumps(d["models"]))
    if key==_lastpub[1] and time.time()-_lastpub[0]<600: return
    try:
        small=dict(d); small["history"]=d["history"][-12:]; today=datetime.datetime.now().strftime("%Y-%m-%d"); small["stats"]={k:v for k,v in stats.items() if k.startswith(today)}
        requests.post(f"https://ntfy.sh/{STOPIC}",data=json.dumps(small).encode(),headers={"Title":"status","Priority":"min"},timeout=10)
        _lastpub[0]=time.time(); _lastpub[1]=key
    except Exception as e: print("status pub fail",e,flush=True)
def event(kind,name,model="256GB Star White"):
    history.append({"t":datetime.datetime.now().isoformat(timespec="seconds"),"kind":kind,"store":name,"model":model}); json.dump(history[-200:],open(HIST,"w"))
def push(msg,title,prio="urgent",tags="iphone",click=None):
    try: requests.post(f"https://ntfy.sh/{TOPIC}",data=msg.encode(),headers={"Title":title,"Priority":prio,"Tags":tags,"Click":click or BUY},timeout=10)
    except Exception as e: print("push fail",e,flush=True)
last={k:False for k in STORES}; fails=0; fail_since=None; warned=False; checks=0
global_dummy=0; blocked=False
WHO='Your PC' if SRC=='pc' else "Vibe Check's computer"
s=requests.Session(); s.headers.update({"User-Agent":UA,"Accept":"application/json"})
OFFSET=0 if ROLE=="primary" else 30
def peer():
    try:
        r=requests.get(f"https://ntfy.sh/{STOPIC}/json?poll=1&since=15m",timeout=10); best=None
        for line in r.text.splitlines():
            try:
                m=json.loads(line)
                if m.get("event")!="message": continue
                d=json.loads(m.get("message","{}"))
                if d.get("src") and d.get("src")!=SRC: best=d
            except Exception: pass
        if not best: return None
        lo=best.get("last_ok")
        if not best.get("ok") or not lo: return None
        if (datetime.datetime.now()-datetime.datetime.fromisoformat(lo)).total_seconds()>660: return None
        return best
    except Exception: return None
def merge(p):
    seen={(h["t"],h["store"],h.get("model")) for h in history}; added=False
    for h in p.get("history",[]):
        if (h["t"],h["store"],h.get("model")) not in seen: history.append(h); added=True
    if added: history.sort(key=lambda h:h["t"]); json.dump(history[-200:],open(HIST,"w"))
def next_slot(after):
    t=time.time()+after; base=t-(t%60)+OFFSET
    while base<t: base+=60
    return base+random.uniform(0,5)-time.time()
GAPS=os.path.join(os.path.dirname(__file__),"gaps.log"); prev_loop=None
while True:
    now=datetime.datetime.now()
    if not (5<=now.hour<22):
        wake=now.replace(hour=5,minute=0,second=0,microsecond=0)
        if now.hour>=22: wake+=datetime.timedelta(days=1)
        print(now,"quiet hours, sleeping until",wake,flush=True)
        try: site_write(False,last,"Paused overnight (10 PM to 5 AM), back at 5 AM")
        except Exception as e: print("pause pub fail",e,flush=True)
        json.dump({"time":now.isoformat(timespec="seconds"),"ok":True,"paused":True},open(STATUS,"w"))
        while datetime.datetime.now()<wake: time.sleep(min(300,max(1,(wake-datetime.datetime.now()).total_seconds())))
        prev_loop=None; continue
    if prev_loop and (now-prev_loop).total_seconds()>600:
        with open(GAPS,"a") as g: g.write(f"{prev_loop.isoformat(timespec='seconds')} -> {now.isoformat(timespec='seconds')} ({int((now-prev_loop).total_seconds()//60)} min, {SRC})\n")
    prev_loop=now
    p=peer()
    if p: merge(p)
    pm={}
    if p:
        for pp,row in zip(MODELS,p.get("models",[])):
            for k,a in zip(STORES,row["a"]): pm[(pp,k)]=bool(a)
    try:
        s=requests.Session(); s.headers.update({"User-Agent":UA,"Accept":"application/json"})
        r=s.get(URL,timeout=15); r.raise_for_status(); ms=r.elapsed.total_seconds()*1000
        stores={x["storeNumber"]:x for x in r.json()["body"]["stores"]}
        cur={}
        for part,mn in MODELS.items():
            if part in ALERTS: continue
            for sn,name in STORES.items():
                a=stores.get(sn,{}).get("partsAvailability",{}).get(part,{}).get("pickupDisplay")=="available"
                if a!=lastm[(part,sn)] and pm.get((part,sn))!=a: event("in" if a else "out",name,mn)
                curm[(part,sn)]=a; lastm[(part,sn)]=a
        for part,(color,buy) in ALERTS.items():
            for sn,name in STORES.items():
                a=stores.get(sn,{}).get("partsAvailability",{}).get(part,{}).get("pickupDisplay")=="available"
                curm[(part,sn)]=a; was=lasta[(part,sn)]; lasta[(part,sn)]=a
                if (part,sn) in pm and pm[(part,sn)]==a: continue
                if a and not was:
                    event("in",name,MODELS[part]); push(f"{color} 256GB is available for pickup at {name}! Tap to buy now.",f"iPhone Duo {color} IN STOCK","urgent","rotating_light,iphone",buy)
                if not a and was:
                    event("out",name,MODELS[part]); push(f"{color} 256GB gone again at {name}.",f"iPhone Duo {color} sold out","default","x",buy)
        for sn in STORES: cur[sn]=any(curm[(p,sn)] for p in ALERTS)
        stat(1,ms); last=cur; checks+=1; last_ok=now.isoformat(timespec="seconds"); site_write(True,cur); fails=0; fail_since=None
        if checks==1: print(now,"first OK check, alerts:",",".join(ALERTS),f"{ms:.0f} ms",flush=True)
        if blocked: push(f"{WHO} is checking Apple again.","Out of the penalty box","default","white_check_mark"); blocked=False
        if warned: push("Apple checks are working again.","Watcher recovered","default","white_check_mark"); warned=False
        json.dump({"time":now.isoformat(timespec="seconds"),"ok":True,"checks":checks,"stores":{STORES[k]:v for k,v in cur.items()}},open(STATUS,"w"))
        delay=next_slot(0)
    except Exception as e:
        fails+=1; fail_since=fail_since or now; stat(0)
        print(now,"error",e,flush=True)
        json.dump({"time":now.isoformat(timespec="seconds"),"ok":False,"error":str(e)[:200],"fails":fails},open(STATUS,"w"))
        if p: print(now,"peer is healthy, not publishing my error",flush=True)
        else: site_write(False,last,"Apple is temporarily blocking checks, retrying")
        if fails==2 and not blocked:
            push(f"Apple is blocking {'your PC' if SRC=='pc' else WHO} ({str(e)[:40]}). It's backing off and will retry; the other machine keeps checking.","Penalty box","default","warning"); blocked=True
        if not warned and not p and (now-fail_since).total_seconds()>900:
            push("Apple has been blocking or failing checks for 15+ minutes. I'm backing off and will keep retrying.","Watcher having trouble","high","warning"); warned=True
        delay=next_slot(min(300,60*2**min(fails-1,3))-60)
    time.sleep(delay)
