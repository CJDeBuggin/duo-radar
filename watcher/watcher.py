import json, random, time, datetime, requests, os
PART="MK1E4LL/A"; ZIP="63117"
STORES={"R114":"Apple Saint Louis Galleria","R062":"Apple West County"}
MODELS={"MK1E4LL/A":"256GB Star White","MK1F4LL/A":"256GB Night Sky","MK1G4LL/A":"512GB Star White","MK1H4LL/A":"512GB Night Sky","MK1J4LL/A":"1TB Star White","MK1L4LL/A":"1TB Night Sky","MK1Q4LL/A":"2TB Star White","MK1R4LL/A":"2TB Night Sky"}
URL="https://www.apple.com/shop/retail/pickup-message?"+"&".join(f"parts.{i}={p}" for i,p in enumerate(MODELS))+f"&location={ZIP}"
lastm={(p,k):False for p in MODELS for k in STORES}; curm=dict(lastm)
BUY="https://www.apple.com/shop/buy-iphone/iphone-duo/7.6-inch-display-256gb-star-white"
TOPIC=open(os.path.join(os.path.dirname(__file__),"topic.txt")).read().strip()
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
STATUS=os.path.join(os.path.dirname(__file__),"status.json")
SITE=os.path.join(os.path.dirname(__file__),"site","status.json")
HIST=os.path.join(os.path.dirname(__file__),"history.json")
try: history=json.load(open(HIST))
except Exception: history=[]
STARTED=datetime.datetime.now().isoformat(timespec="seconds")
last_ok=None
def site_write(ok,cur,err=None):
    d={"now":datetime.datetime.now().isoformat(timespec="seconds"),"ok":ok,"last_ok":last_ok,"started":STARTED,"checks":checks,
       "product":"iPhone Duo 256GB Star White","buy":BUY,"error":err,
       "stores":[{"id":k,"name":v,"available":bool(cur.get(k))} for k,v in STORES.items()],"history":history[-25:],
       "models":[{"m":MODELS[p],"a":[1 if curm.get((p,k)) else 0 for k in STORES]} for p in MODELS]}
    tmp=SITE+".tmp"; json.dump(d,open(tmp,"w")); os.replace(tmp,SITE); pub_status(d)
STOPIC=open(os.path.join(os.path.dirname(__file__),"status_topic.txt")).read().strip()
_lastpub=[0,None]
def pub_status(d):
    key=(d["ok"],tuple(x["available"] for x in d["stores"]),len(d["history"]),json.dumps(d["models"]))
    if key==_lastpub[1] and time.time()-_lastpub[0]<600: return
    try:
        small=dict(d); small["history"]=d["history"][-12:]
        requests.post(f"https://ntfy.sh/{STOPIC}",data=json.dumps(small).encode(),headers={"Title":"status","Priority":"min"},timeout=10)
        _lastpub[0]=time.time(); _lastpub[1]=key
    except Exception as e: print("status pub fail",e,flush=True)
def event(kind,name,model="256GB Star White"):
    history.append({"t":datetime.datetime.now().isoformat(timespec="seconds"),"kind":kind,"store":name,"model":model}); json.dump(history[-200:],open(HIST,"w"))
def push(msg,title,prio="urgent",tags="iphone"):
    try: requests.post(f"https://ntfy.sh/{TOPIC}",data=msg.encode(),headers={"Title":title,"Priority":prio,"Tags":tags,"Click":BUY},timeout=10)
    except Exception as e: print("push fail",e,flush=True)
last={k:False for k in STORES}; fails=0; fail_since=None; warned=False; checks=0
global_dummy=0
s=requests.Session(); s.headers.update({"User-Agent":UA,"Accept":"application/json"})
while True:
    now=datetime.datetime.now()
    try:
        s=requests.Session(); s.headers.update({"User-Agent":UA,"Accept":"application/json"})
        r=s.get(URL,timeout=15); r.raise_for_status()
        stores={x["storeNumber"]:x for x in r.json()["body"]["stores"]}
        cur={}
        for p,mn in MODELS.items():
            if p==PART: continue
            for sn,name in STORES.items():
                a=stores.get(sn,{}).get("partsAvailability",{}).get(p,{}).get("pickupDisplay")=="available"
                if a and not lastm[(p,sn)]: event("in",name,mn)
                if not a and lastm[(p,sn)]: event("out",name,mn)
                curm[(p,sn)]=a; lastm[(p,sn)]=a
        for sn,name in STORES.items():
            p=stores.get(sn,{}).get("partsAvailability",{}).get(PART,{})
            cur[sn]=p.get("pickupDisplay")=="available"; curm[(PART,sn)]=cur[sn]
            if cur[sn] and not last[sn]:
                event("in",name); push(f"Star White 256GB is available for pickup at {name}! Tap to buy now.","iPhone Duo IN STOCK","urgent","rotating_light,iphone")
            if not cur[sn] and last[sn]:
                event("out",name); push(f"Gone again at {name}.","iPhone Duo sold out","default","x")
        last=cur; checks+=1; last_ok=now.isoformat(timespec="seconds"); site_write(True,cur); fails=0; fail_since=None
        if warned: push("Apple checks are working again.","Watcher recovered","default","white_check_mark"); warned=False
        json.dump({"time":now.isoformat(timespec="seconds"),"ok":True,"checks":checks,"stores":{STORES[k]:v for k,v in cur.items()}},open(STATUS,"w"))
        delay=random.uniform(18,26)
    except Exception as e:
        fails+=1; fail_since=fail_since or now
        print(now,"error",e,flush=True)
        json.dump({"time":now.isoformat(timespec="seconds"),"ok":False,"error":str(e)[:200],"fails":fails},open(STATUS,"w"))
        site_write(False,last,"Apple is temporarily blocking checks, retrying")
        if not warned and (now-fail_since).total_seconds()>900:
            push("Apple has been blocking or failing checks for 15+ minutes. I'm backing off and will keep retrying.","Watcher having trouble","high","warning"); warned=True
        delay=min(300,30*2**min(fails-1,4))
    time.sleep(delay)
