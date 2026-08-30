#!/usr/bin/env python3
"""RogueForge 0.8.2 — single-file Docker/Podman Compose operations runtime."""
from __future__ import annotations

import base64, hashlib, hmac, json, mimetypes, os, re, secrets, socket, subprocess, sys, threading, time
from http.client import HTTPConnection
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

VERSION="0.8.2"
PORT=int(os.environ.get("ROGUEFORGE_PORT","7810")); BIND=os.environ.get("ROGUEFORGE_BIND","127.0.0.1")
STACKS_DIR=Path(os.environ.get("ROGUEFORGE_STACKS_DIR","/opt/media-server")).resolve(); STATIC_DIR=Path(os.environ.get("ROGUEFORGE_STATIC_DIR",Path(__file__).with_name("static"))).resolve()
ENGINE=os.environ.get("ROGUEFORGE_ENGINE","auto").strip().lower(); SOCKET_PATH=os.environ.get("ROGUEFORGE_SOCKET","").strip(); PODMAN_REMOTE=os.environ.get("ROGUEFORGE_PODMAN_REMOTE","").strip().lower() in ("1","true","yes")
PUBLIC_URL=os.environ.get("ROGUEFORGE_PUBLIC_URL","").strip(); ICONS_DIR=Path(os.environ.get("ROGUEFORGE_ICONS_DIR","/opt/media-server/rogue-dashboard/app/static/icons")).resolve(); AUTH_FILE=Path(os.environ.get("ROGUEFORGE_AUTH_FILE",Path(__file__).with_name("data")/"auth.json")).resolve()
SELF_STACK=os.environ.get("ROGUEFORGE_SELF_STACK","rogueforge").strip(); SESSION_TTL=int(os.environ.get("ROGUEFORGE_SESSION_TTL","43200")); DEMO_MODE=os.environ.get("ROGUEFORGE_DEMO","").strip().lower() in ("1","true","yes")
SCAN_DEPTH=max(1,min(12,int(os.environ.get("ROGUEFORGE_SCAN_DEPTH","4")))); CACHE_SECONDS=max(2,min(300,int(os.environ.get("ROGUEFORGE_DISCOVERY_CACHE","10"))))
COMPOSE_NAMES=("podman-compose.yaml","compose.podman.yaml","docker-compose.yaml","docker-compose.yml","compose.yaml","compose.yml")
EXCLUDED_DIRS={".git",".cache","node_modules","__pycache__","backup","backups"}; MAX_BODY=2_000_000; LOGIN_WINDOW=300; LOGIN_LIMIT=8
_sessions={}; _login_attempts={}; _login_lock=threading.Lock(); _runtime=None; _discovery_cache={"time":0.0,"records":[],"aliases":{},"by_dir":{}}
_terminal_sessions={}; _terminal_lock=threading.Lock(); TERMINAL_TTL=1800; TERMINAL_CLOSED_GRACE=60; MAX_TERMINAL_CHUNKS=2500
OPERATIONS_FILE=Path(os.environ.get("ROGUEFORGE_OPERATIONS_FILE",Path(__file__).with_name("data")/"operations.json")).resolve()
_operation_lock=threading.Lock(); _operations={}; MAX_OPERATIONS=120
OPERATION_TIMEOUT=max(60,min(7200,int(os.environ.get("ROGUEFORGE_OPERATION_TIMEOUT","900"))))
OPERATION_TERMINATE_GRACE=max(2,min(60,int(os.environ.get("ROGUEFORGE_OPERATION_TERMINATE_GRACE","10"))))
def _load_operations():
    global _operations
    try:
        rows=json.loads(OPERATIONS_FILE.read_text(encoding="utf-8"));_operations={str(x["id"]):x for x in rows if isinstance(x,dict) and x.get("id")}
        for x in _operations.values():
            if x.get("status")=="running":x["status"]="interrupted";x["ended"]=time.time()
    except Exception:_operations={}
def _save_operations():
    try:
        OPERATIONS_FILE.parent.mkdir(parents=True,exist_ok=True)
        rows=sorted(_operations.values(),key=lambda x:x.get("started",0),reverse=True)[:MAX_OPERATIONS]
        tmp=OPERATIONS_FILE.with_suffix(".tmp");tmp.write_text(json.dumps(rows,indent=2),encoding="utf-8");tmp.replace(OPERATIONS_FILE)
    except Exception:pass
def _op_public(x):
    return {k:v for k,v in x.items() if k!="process"}
def operation_list():
    with _operation_lock:return [_op_public(x) for x in sorted(_operations.values(),key=lambda x:x.get("started",0),reverse=True)[:MAX_OPERATIONS]]
def operation_get(oid):
    with _operation_lock:
        x=_operations.get(oid)
        if not x:raise FileNotFoundError("operation")
        return _op_public(x)
def _op_append(oid,text):
    if not text:return
    with _operation_lock:
        x=_operations.get(oid)
        if x:x["output"]=(x.get("output","")+str(text))[-100000:];_save_operations()
def _op_compose(oid,stack,args,timeout=None):
    timeout=OPERATION_TIMEOUT if timeout is None else max(1,int(timeout))
    with _operation_lock:op=dict(_operations.get(oid) or {})
    # Pin operations to the exact Compose path captured when the operation starts.
    # This prevents a compose down from making subsequent start/restart/update
    # dependent on live container-label discovery.
    d=Path(op.get("directory") or safe_stack(stack)).resolve();cf=Path(op.get("composePath") or compose_file(d)).resolve()
    if not cf.is_file():raise RuntimeError("compose file not found")
    rt=runtime();env=os.environ.copy()
    try:ef=stack_env_path(stack)
    except Exception:ef=d/".env"
    if rt["engine"]=="podman":
        if PODMAN_REMOTE:env=podman_remote_env()
        env["PODMAN_COMPOSE_WARNING_LOGS"]="false";env["PODMAN_COMPOSE_IN_POD"]="false"
        if ef.is_file():
            for line in ef.read_text(encoding="utf-8",errors="replace").splitlines():
                line=line.strip()
                if not line or line.startswith("#") or "=" not in line:continue
                key,value=line.split("=",1);key=key.strip()
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$",key):
                    value=value.strip()
                    if len(value)>=2 and value[0]==value[-1] and value[0] in ("'",'"'):value=value[1:-1]
                    env[key]=value
        cmd=[os.environ.get("ROGUEFORGE_PODMAN_COMPOSE","/usr/bin/podman-compose"),"-f",str(cf)]+args
    else:
        env["DOCKER_HOST"]=f"unix://{rt['socket']}";cmd=["/usr/bin/docker","compose"]
        if ef.is_file():cmd += ["--env-file",str(ef)]
        cmd += ["-f",str(cf)]+args
    p=subprocess.Popen(cmd,cwd=d,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1)
    with _operation_lock:
        x=_operations.get(oid)
        if x:x["process"]=p;x["timeoutSeconds"]=timeout;_save_operations()
    timed_out=threading.Event()
    def expire():
        if p.poll() is not None:return
        timed_out.set()
        with _operation_lock:
            x=_operations.get(oid)
            if x:x["timedOut"]=True;_save_operations()
        _op_append(oid,f"\nTIMEOUT: command exceeded {timeout}s; terminating process.\n")
        try:p.terminate()
        except Exception:pass
    timer=threading.Timer(timeout,expire);timer.daemon=True;timer.start()
    try:
        for line in iter(p.stdout.readline,""):
            _op_append(oid,line)
            with _operation_lock:cancel=bool(_operations.get(oid,{}).get("cancelRequested"))
            if cancel and p.poll() is None:
                try:p.terminate()
                except Exception:pass
        try:rc=p.wait(timeout=OPERATION_TERMINATE_GRACE)
        except subprocess.TimeoutExpired:
            try:p.kill()
            except Exception:pass
            rc=p.wait(timeout=OPERATION_TERMINATE_GRACE)
        with _operation_lock:cancel=bool(_operations.get(oid,{}).get("cancelRequested"))
        if timed_out.is_set():raise TimeoutError(f"operation timed out after {timeout}s")
        if cancel:raise InterruptedError("operation cancelled")
        if rc:raise RuntimeError(f"Compose command failed ({rc})")
    finally:
        timer.cancel()
        with _operation_lock:
            if oid in _operations:_operations[oid].pop("process",None);_save_operations()
def _operation_worker(oid):
    with _operation_lock:x=_operations[oid];scope=x["scope"];target=x["target"];action=x["action"]
    status="failed";failure=None
    try:
        if scope!="stack":raise ValueError("unsupported operation scope")
        steps={"start":[["up","-d"]],"stop":[["down"]],"restart":[["down"],["up","-d"]],"pull":[["pull"]],"recreate":[["up","-d","--force-recreate"]],"update":[["pull"],["down"],["up","-d"]]}[action]
        safe_stack(target)
        with _operation_lock:
            x=_operations[oid];x["stepCount"]=len(steps);_save_operations()
        for index,args in enumerate(steps,1):
            with _operation_lock:
                x=_operations[oid]
                if x.get("cancelRequested"):raise InterruptedError("operation cancelled")
                x["stepIndex"]=index;x["currentStep"]=" ".join(args);x["stepStarted"]=time.time();_save_operations()
            _op_append(oid,f"$ compose {' '.join(args)}\n");_op_compose(oid,target,args)
        invalidate_inventory();_build_registry(force=True)
        status="success"
    except TimeoutError as e:failure=str(e);_op_append(oid,"ERROR: "+failure+"\n");status="timed_out"
    except InterruptedError as e:failure=str(e);_op_append(oid,failure+"\n");status="cancelled"
    except Exception as e:failure=str(e);_op_append(oid,"ERROR: "+failure+"\n");status="failed"
    with _operation_lock:
        x=_operations.get(oid)
        if x:
            x["status"]=status;x["ended"]=time.time();x["failureReason"]=failure;x["currentStep"]=None;x["stepStarted"]=None;x.pop("process",None);_save_operations()
def start_operation(scope,target,action):
    if scope!="stack" or action not in ("start","stop","restart","pull","recreate","update"):raise ValueError("unsupported operation")
    rec=resolve_stack(target);safe_stack(target);d=rec["directory"].resolve();cf=rec["compose"].resolve()
    oid=secrets.token_urlsafe(12);x={"id":oid,"scope":scope,"target":target,"action":action,"directory":str(d),"composePath":str(cf),"status":"running","started":time.time(),"ended":None,"output":"","cancelRequested":False,"timedOut":False,"timeoutSeconds":OPERATION_TIMEOUT,"stepIndex":0,"stepCount":0,"currentStep":None,"stepStarted":None,"failureReason":None}
    with _operation_lock:_operations[oid]=x;_save_operations()
    threading.Thread(target=_operation_worker,args=(oid,),daemon=True).start();return _op_public(x)
def cancel_operation(oid):
    with _operation_lock:
        x=_operations.get(oid)
        if not x:raise FileNotFoundError("operation")
        if x.get("status")!="running":return _op_public(x)
        x["cancelRequested"]=True;p=x.get("process");_save_operations()
    if p and p.poll() is None:
        try:p.terminate()
        except Exception:pass
    return operation_get(oid)
_load_operations()

def _unb64(v): return base64.urlsafe_b64decode(v+"="*(-len(v)%4))
def load_auth():
    try:
        d=json.loads(AUTH_FILE.read_text(encoding="utf-8")); return d if all(d.get(k) for k in ("username","salt","passwordHash")) else None
    except Exception: return None
def auth_diagnostics():
    a=load_auth(); return {"path":str(AUTH_FILE),"exists":AUTH_FILE.is_file(),"readable":os.access(AUTH_FILE,os.R_OK) if AUTH_FILE.exists() else False,"valid":bool(a),"username":a.get("username") if a else None}
def verify_password(password,auth):
    try: return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256",str(password).encode(),_unb64(auth["salt"]),int(auth.get("iterations",600000))),_unb64(auth["passwordHash"]))
    except Exception: return False
def make_session(auth):
    token=secrets.token_urlsafe(32); session={"user":auth["username"],"csrf":secrets.token_urlsafe(24),"expires":time.time()+SESSION_TTL}; _sessions[token]=session; return token,session
def read_session(token,auth):
    s=_sessions.get(token)
    if not s or s["expires"]<time.time() or s["user"]!=auth["username"]: _sessions.pop(token,None); return None
    s["expires"]=time.time()+SESSION_TTL; return s
def login_allowed(client,success=None):
    now=time.time()
    with _login_lock:
        recent=[t for t in _login_attempts.get(client,[]) if now-t<LOGIN_WINDOW]
        if success is True: _login_attempts.pop(client,None); return True
        if success is False: recent.append(now); _login_attempts[client]=recent
        return len(recent)<LOGIN_LIMIT

class UnixHTTPConnection(HTTPConnection):
    def __init__(self,path): super().__init__("localhost",timeout=5); self.path=path
    def connect(self): self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); self.sock.settimeout(self.timeout); self.sock.connect(self.path)
def request_socket(sock,method,path,body=None,maximum=5_000_000):
    c=UnixHTTPConnection(sock)
    try:
        c.request(method,path,body=body,headers={"Accept":"application/json"}); r=c.getresponse(); raw=r.read(maximum)
        if r.status>=400: raise RuntimeError(f"engine HTTP {r.status}: {raw[:500].decode(errors='replace')}")
        if not raw:return None
        return json.loads(raw) if "json" in r.getheader("content-type","") or raw[:1] in (b"{",b"[") else raw.decode(errors="replace")
    finally:c.close()
def runtime():
    global _runtime
    if _runtime:return _runtime
    if DEMO_MODE:_runtime={"engine":"demo","socket":"simulated","version":"demo","apiVersion":"demo","context":"demo"};return _runtime
    errors=[]
    for path in list(dict.fromkeys(([SOCKET_PATH] if SOCKET_PATH else [])+["/run/podman/podman.sock","/var/run/docker.sock"])):
        if not Path(path).exists():errors.append(f"missing {path}");continue
        try:
            d=request_socket(path,"GET","/version",maximum=200000) or {}; blob=json.dumps(d).lower(); kind="podman" if "podman" in blob or "libpod" in blob else "docker"
            if ENGINE not in ("auto",kind):continue
            _runtime={"engine":kind,"socket":path,"version":str(d.get("Version") or d.get("version") or "unknown"),"apiVersion":str(d.get("ApiVersion") or d.get("APIVersion") or "unknown"),"context":"remote socket" if kind=="podman" and PODMAN_REMOTE else "socket"}; return _runtime
        except Exception as e:errors.append(f"{path}: {e}")
    raise RuntimeError("No matching Docker/Podman API socket detected ("+"; ".join(errors)+")")
def request_engine(method,path,body=None,maximum=5_000_000):return request_socket(runtime()["socket"],method,path,body,maximum)
def podman_remote_env():
    e=os.environ.copy(); u=f"unix://{runtime()['socket']}"; e["CONTAINER_HOST"]=u;e["DOCKER_HOST"]=u;return e
def podman_remote_command(args,timeout=60):
    p=subprocess.run([os.environ.get("ROGUEFORGE_PODMAN","/usr/bin/podman"),"--remote","--url",f"unix://{runtime()['socket']}"]+args,text=True,capture_output=True,timeout=timeout)
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-20000:] or "Remote Podman command failed")
    return p.stdout
def engine_cli(args,timeout=900):
    if runtime()["engine"]=="podman":return podman_remote_command(args,timeout)
    e=os.environ.copy();e["DOCKER_HOST"]=f"unix://{runtime()['socket']}";p=subprocess.run(["/usr/bin/docker"]+args,env=e,text=True,capture_output=True,timeout=timeout);o=(p.stdout+p.stderr)[-100000:]
    if p.returncode:raise RuntimeError(o or "Docker command failed")
    return o

def load_containers():
    if DEMO_MODE:return []
    if runtime()["engine"]=="podman" and PODMAN_REMOTE:
        try:
            d=json.loads(podman_remote_command(["ps","-a","--format","json"],30) or "[]");
            if isinstance(d,list):return d
        except Exception as e:sys.stderr.write(f"remote Podman inventory failed; API fallback: {e}\n")
    eps=["/containers/json?all=1"]
    if runtime()["engine"]=="podman":
        v=runtime()["version"].split("-")[0];a=runtime()["apiVersion"];eps=[f"/v{v}/libpod/containers/json?all=true",f"/v{a}/libpod/containers/json?all=true","/libpod/containers/json?all=true"]+eps
    errors=[]
    for ep in eps:
        try:
            d=request_engine("GET",ep)
            if d is not None:return d
        except Exception as e:errors.append(str(e))
    raise RuntimeError("Unable to list containers: "+"; ".join(errors))
def _raw_container(cid):
    for x in load_containers() or []:
        actual=str(x.get("Id") or x.get("ID") or x.get("id") or "")
        if actual.lower().startswith(cid.lower()):return x
    raise FileNotFoundError("container")
def _container_meta(cid):
    x=_raw_container(cid); labels=x.get("Labels") or x.get("labels") or {}; labels=labels if isinstance(labels,dict) else {}; names=x.get("Names") or x.get("names") or []; names=[names] if isinstance(names,str) else names
    name=names[0].lstrip("/") if names else str(x.get("Name") or x.get("name") or "unnamed"); project=labels.get("com.docker.compose.project") or labels.get("io.podman.compose.project") or "standalone"; service=labels.get("com.docker.compose.service") or labels.get("io.podman.compose.service") or ""; image=x.get("Image") or x.get("ImageName") or x.get("image") or "unknown"; fid=str(x.get("Id") or x.get("ID") or x.get("id") or cid)
    meta={"id":fid,"shortId":fid[:12],"name":name,"image":image,"project":str(project),"service":str(service),"composeManaged":bool(service and project!="standalone"),"selfProtected":name==SELF_STACK or str(project)==SELF_STACK,"labels":labels}
    try:
        rec=resolve_stack(str(project)) if project!="standalone" else None
        if rec:meta.update(project=rec["key"],projectDisplay=rec.get("project") or rec["directory"].name,composePath=str(rec["compose"]),composeManaged=bool(service),discoverySource=rec["source"])
    except Exception:pass
    return meta
def containers():
    result=[]
    for x in load_containers() or []:
        fid=str(x.get("Id") or x.get("ID") or x.get("id") or "")
        try:m=_container_meta(fid[:12]); state=str(x.get("State") or x.get("state") or "unknown").lower();result.append({"id":fid[:12],"name":m["name"],"image":m["image"],"state":state,"status":x.get("Status") or x.get("status") or state,"ports":x.get("Ports") or x.get("ports") or [],"project":m["project"],"service":m["service"] or None,"composeManaged":m["composeManaged"],"selfProtected":m["selfProtected"]})
        except Exception:pass
    return sorted(result,key=lambda i:(i["state"]!="running",i["name"].lower()))

def _inside_root(p):
    try:p.resolve().relative_to(STACKS_DIR);return True
    except ValueError:return False
def _norm(v):return (re.sub(r"[^A-Za-z0-9._-]+","--",str(v).strip().strip("/"))[:127] or "stack")
def _compose_basic(d):
    for n in COMPOSE_NAMES:
        p=d/n
        if p.is_file():return p
    return None
def _label_compose(labels):
    for k in ("com.docker.compose.project.config_files","io.podman.compose.project.config_files","com.docker.compose.project.config_file","io.podman.compose.project.config_file"):
        for item in str(labels.get(k) or "").split(","):
            if item.strip():
                p=Path(item.strip()).resolve()
                if p.is_file() and _inside_root(p):return p
    return None
def _label_workdir(labels):
    for k in ("com.docker.compose.project.working_dir","io.podman.compose.project.working_dir","com.docker.compose.project.working-directory"):
        if labels.get(k):
            p=Path(str(labels[k])).resolve()
            if p.is_dir() and _inside_root(p):return p
    return None
def _build_registry(force=False):
    now=time.time()
    if not force and now-_discovery_cache["time"]<CACHE_SECONDS:return _discovery_cache
    records={}
    def add(directory,compose,project=None,source="scan"):
        directory=directory.resolve();compose=compose.resolve()
        if not _inside_root(directory) or not compose.is_file():return
        k=str(directory); rel=directory.relative_to(STACKS_DIR); cur=records.get(k)
        if cur:
            if project and not cur.get("project"):cur["project"]=project
            if source=="labels":cur["source"]="labels"
            return
        records[k]={"key":_norm(str(rel) if str(rel)!="." else directory.name),"directory":directory,"compose":compose,"project":project or None,"source":source,"relativePath":str(rel)}
    try:
        for x in load_containers() or []:
            labels=x.get("Labels") or x.get("labels") or {}; labels=labels if isinstance(labels,dict) else {}; project=labels.get("com.docker.compose.project") or labels.get("io.podman.compose.project"); cf=_label_compose(labels); wd=_label_workdir(labels)
            if cf:add(cf.parent,cf,str(project) if project else None,"labels")
            elif wd:
                c=_compose_basic(wd)
                if c:add(wd,c,str(project) if project else None,"labels")
    except Exception:pass
    if STACKS_DIR.is_dir():
        for cur,dirs,files in os.walk(STACKS_DIR):
            p=Path(cur); depth=len(p.relative_to(STACKS_DIR).parts); dirs[:]=[d for d in dirs if not d.startswith(".") and d.lower() not in EXCLUDED_DIRS];
            if depth>=SCAN_DEPTH:dirs[:]=[]
            for n in COMPOSE_NAMES:
                if n in files:add(p,p/n);break
    items=list(records.values()); used=set()
    for r in items:
        base=_norm(r.get("project") or r["key"]); key=base; i=2
        while key in used:key=f"{base}-{i}"[:127];i+=1
        r["key"]=key;used.add(key)
    aliases={};by_dir={}
    for r in items:
        by_dir[str(r["directory"])]=r
        for a in (r["key"],r.get("project"),r["directory"].name,r["relativePath"]):
            if a:aliases.setdefault(str(a),r)
    _discovery_cache.update(time=now,records=items,aliases=aliases,by_dir=by_dir);return _discovery_cache
def resolve_stack(value):
    reg=_build_registry(); r=reg["aliases"].get(str(value)) or reg["aliases"].get(_norm(value))
    if not r:raise FileNotFoundError(str(value))
    return r
def safe_stack(value,allow_self=False):
    r=resolve_stack(value); ids={r["key"],r.get("project"),r["directory"].name}
    if SELF_STACK in ids and not allow_self:raise PermissionError("RogueForge cannot manage its own Compose project from inside itself")
    return r["directory"]
def compose_file(directory):return _build_registry()["by_dir"].get(str(directory.resolve()),{}).get("compose") or _compose_basic(directory)
def discover_stacks():
    reg=_build_registry(force=True); members={}
    for c in containers():members.setdefault(c.get("project","standalone"),[]).append(c)
    out=[]
    for r in sorted(reg["records"],key=lambda x:x["key"].lower()):
        g=members.get(r["key"],[]); running=sum(x["state"]=="running" for x in g); ids={r["key"],r.get("project"),r["directory"].name}
        out.append({"name":r["key"],"displayName":r.get("project") or r["directory"].name,"composeFile":r["compose"].name,"relativePath":r["relativePath"],"discoverySource":r["source"],"hasEnv":(r["directory"]/".env").is_file(),"engineHint":"podman" if "podman" in r["compose"].name else ("docker" if "docker" in r["compose"].name else "portable"),"services":len(g),"running":running,"state":"running" if g and running==len(g) else ("partial" if running else "stopped"),"managed":SELF_STACK not in ids})
    return out
def discovery_diagnostics():
    r=_build_registry(force=True);return {"scanDepth":SCAN_DEPTH,"cacheSeconds":CACHE_SECONDS,"stacksRoot":str(STACKS_DIR),"discovered":len(r["records"]),"stacks":[{"key":x["key"],"project":x.get("project"),"directory":str(x["directory"]),"compose":str(x["compose"]),"source":x["source"]} for x in r["records"]]}

def compose_command(stack,args):
    d=safe_stack(stack);cf=compose_file(d)
    if not cf:raise RuntimeError("compose file not found")
    rt=runtime();env=os.environ.copy()
    if rt["engine"]=="podman":
        if PODMAN_REMOTE:env=podman_remote_env()
        cmd=[os.environ.get("ROGUEFORGE_PODMAN_COMPOSE","/usr/bin/podman-compose"),"-f",str(cf)]
    else:
        env["DOCKER_HOST"]=f"unix://{rt['socket']}";cmd=[os.environ.get("ROGUEFORGE_DOCKER_COMPOSE","/usr/bin/docker-compose")]
        if (d/".env").is_file():cmd += ["--env-file",str(d/".env")]
        cmd += ["-f",str(cf)]
    return d,cmd+args,env
def run_compose(stack,args,timeout=900):
    if args==["config"]:return validate_stack(stack,timeout)
    d,cmd,env=compose_command(stack,args);p=subprocess.run(cmd,cwd=d,env=env,text=True,capture_output=True,timeout=timeout);o=(p.stdout+p.stderr)[-100000:]
    if p.returncode:raise RuntimeError(o or f"Compose command failed ({p.returncode})")
    return o
def validate_stack(name,timeout=60):
    if runtime()["engine"]!="podman":
        d,cmd,env=compose_command(name,["config"])
    else:
        d,cmd,env=compose_command(name,[]);cmd += ["--dry-run","up"]
    p=subprocess.run(cmd,cwd=d,env=env,text=True,capture_output=True,timeout=timeout);o=(p.stdout+p.stderr)[-100000:]
    if p.returncode:raise RuntimeError(o or f"Compose validation failed ({p.returncode})")
    return o
def run_stack_action(stack,action):
    m={"start":["up","-d"],"stop":["stop"],"restart":["restart"],"pull":["pull"],"recreate":["up","-d","--force-recreate"]}
    if action not in m:raise ValueError("unsupported action")
    safe_stack(stack);return {"ok":True,"output":run_compose(stack,m[action])}
def update_stack(name):return {"ok":True,"output":(run_compose(name,["pull"])+"\n"+run_compose(name,["up","-d","--remove-orphans"]))[-100000:]}
def stack_env(name):
    p=safe_stack(name)/".env";return {"name":".env","exists":p.is_file(),"content":p.read_text(encoding="utf-8") if p.is_file() else ""}
def save_stack_env(name,content):
    if not isinstance(content,str) or len(content.encode())>1_000_000:raise ValueError("invalid environment content")
    p=safe_stack(name)/".env";backup=None
    if p.is_file():backup=p.with_name(f".env.rogueforge-{int(time.time())}.bak");backup.write_bytes(p.read_bytes())
    p.write_text(content,encoding="utf-8")
    try:validate_stack(name)
    except Exception:
        if backup and backup.is_file():p.write_bytes(backup.read_bytes())
        else:p.unlink(missing_ok=True)
        raise
    return {"ok":True,"backup":backup.name if backup else None}

def inspect_container(cid):
    m=_container_meta(cid);d=json.loads(engine_cli(["inspect",m["id"]],60) or "[]");x=d[0] if isinstance(d,list) and d else d;s=x.get("State") or {};cfg=x.get("Config") or {};hc=x.get("HostConfig") or {};net=x.get("NetworkSettings") or {};rp=hc.get("RestartPolicy") or {};rp={"Name":rp} if isinstance(rp,str) else rp
    return {**{k:m[k] for k in ("id","shortId","name","image","project","service","composeManaged","selfProtected")},"created":x.get("Created"),"status":s.get("Status"),"running":s.get("Running"),"startedAt":s.get("StartedAt"),"finishedAt":s.get("FinishedAt"),"restartCount":x.get("RestartCount",0),"restartPolicy":rp.get("Name") or rp.get("name") or "none","imageId":x.get("Image"),"command":cfg.get("Cmd") or [],"entrypoint":cfg.get("Entrypoint") or [],"mounts":[{"source":a.get("Source"),"destination":a.get("Destination"),"type":a.get("Type"),"rw":a.get("RW")} for a in x.get("Mounts") or []],"networks":list((net.get("Networks") or {}).keys())}
def container_stats():
    try:
        raw=engine_cli(["stats","--no-stream","--format","json"],60);rows=[]
        for line in raw.splitlines():
            try:rows.append(json.loads(line))
            except Exception:pass
        if len(rows)==1 and isinstance(rows[0],list):rows=rows[0]
        return {(str(r.get("id") or r.get("ID") or r.get("Container") or "")[:12] or str(r.get("name") or r.get("Name") or "")):{"cpu":r.get("cpu_percent") or r.get("CPUPerc") or r.get("CPU"),"memory":r.get("mem_usage") or r.get("MemUsage"),"memoryPercent":r.get("mem_percent") or r.get("MemPerc"),"network":r.get("net_io") or r.get("NetIO"),"block":r.get("block_io") or r.get("BlockIO"),"pids":r.get("pids") or r.get("PIDs")} for r in rows}
    except Exception:return {}
def image_status(cid,pull=False):
    m=_container_meta(cid);before=inspect_container(cid).get("imageId");output=engine_cli(["pull",m["image"]],900) if pull else ""
    try:d=json.loads(engine_cli(["image","inspect",m["image"]],60) or "[]");x=d[0] if isinstance(d,list) and d else d;current=x.get("Id") or x.get("ID")
    except Exception:current=None
    return {"id":m["id"],"name":m["name"],"image":m["image"],"containerImageId":before,"localImageId":current,"updateAvailable":bool(before and current and before!=current),"checkedByPull":pull,"output":output[-100000:]}
def _mutable(m,action):
    if m["selfProtected"]:raise PermissionError(f"RogueForge cannot {action} its own container from inside itself")
def container_action(cid,action):
    m=_container_meta(cid);_mutable(m,action)
    if action in ("start","stop","restart"):
        engine_cli(([action,"--time","10",m["id"]] if action in ("stop","restart") and runtime()["engine"]=="podman" else [action,m["id"]]),60);return {"ok":True}
    if action=="check-update":return image_status(cid,True)
    if action=="update":
        if not m["composeManaged"]:return {"ok":True,"output":engine_cli(["pull",m["image"]],900),"recreated":False,"message":"Image pulled; standalone container not automatically recreated."}
        return {"ok":True,"output":(run_compose(m["project"],["pull",m["service"]])+"\n"+run_compose(m["project"],["up","-d","--no-deps","--remove-orphans",m["service"]]))[-100000:],"recreated":True}
    if action=="recreate":
        if not m["composeManaged"]:raise RuntimeError("Recreate is only available for Compose-managed containers")
        return {"ok":True,"output":run_compose(m["project"],["up","-d","--no-deps","--force-recreate",m["service"]])}
    if action=="remove":
        return {"ok":True,"output":run_compose(m["project"],["rm","-s","-f",m["service"]],300) if m["composeManaged"] else engine_cli(["rm","-f",m["id"]],300)}
    raise ValueError("unsupported action")
def bulk_container_action(ids,action):
    if action not in ("start","stop","restart","update","recreate","remove") or not isinstance(ids,list) or not ids or len(ids)>100:raise ValueError("invalid bulk operation")
    results=[]
    for cid in ids:
        try:m=_container_meta(str(cid));r=container_action(str(cid),action);results.append({"id":str(cid),"name":m["name"],"ok":True,"message":r.get("message"),"output":r.get("output","")[-4000:]})
        except Exception as e:results.append({"id":str(cid),"ok":False,"error":str(e)})
    return {"ok":all(x["ok"] for x in results),"action":action,"results":results}
def _json_rows(raw):
    raw=(raw or "").strip()
    if not raw:return []
    try:
        parsed=json.loads(raw)
        if isinstance(parsed,list):return parsed
        if isinstance(parsed,dict):return [parsed]
    except Exception:pass
    rows=[]
    for line in raw.splitlines():
        try:
            parsed=json.loads(line)
            rows.extend(parsed if isinstance(parsed,list) else [parsed])
        except Exception:pass
    return [r for r in rows if isinstance(r,dict)]
def resource_images():
    rows=_json_rows(engine_cli(["images","--format","json"],60));out=[]
    for r in rows:
        repo=str(r.get("Repository") or r.get("repository") or r.get("Repo") or "<none>")
        tag=str(r.get("Tag") or r.get("tag") or "<none>")
        rid=str(r.get("Id") or r.get("ID") or r.get("id") or r.get("ImageID") or "")
        names=r.get("Names") or r.get("RepoTags") or []
        if (repo=="<none>" or tag=="<none>") and isinstance(names,list) and names:
            first=str(names[0])
            if ":" in first:repo,tag=first.rsplit(":",1)
            else:repo=first
        out.append({"id":rid,"shortId":rid.replace("sha256:","")[:12],"repository":repo,"tag":tag,"created":r.get("Created") or r.get("CreatedAt") or r.get("created"),"size":r.get("Size") or r.get("size") or r.get("VirtualSize"),"digest":r.get("Digest") or r.get("digest")})
    return sorted(out,key=lambda x:(x["repository"].lower(),x["tag"].lower()))
def resource_volumes():
    rows=_json_rows(engine_cli(["volume","ls","--format","json"],60));out=[]
    for r in rows:
        name=str(r.get("Name") or r.get("name") or r.get("VolumeName") or "")
        if not name:continue
        out.append({"name":name,"driver":r.get("Driver") or r.get("driver") or "local","scope":r.get("Scope") or r.get("scope") or "local","mountpoint":r.get("Mountpoint") or r.get("mountpoint"),"created":r.get("CreatedAt") or r.get("Created") or r.get("created"),"labels":r.get("Labels") or r.get("labels") or {}})
    return sorted(out,key=lambda x:x["name"].lower())
def resource_networks():
    rows=_json_rows(engine_cli(["network","ls","--format","json"],60));out=[]
    for r in rows:
        name=str(r.get("Name") or r.get("name") or "")
        if not name:continue
        rid=str(r.get("Id") or r.get("ID") or r.get("id") or "")
        out.append({"id":rid,"shortId":rid[:12],"name":name,"driver":r.get("Driver") or r.get("driver") or "bridge","scope":r.get("Scope") or r.get("scope") or "local","ipv6":bool(r.get("IPv6") or r.get("ipv6")),"internal":bool(r.get("Internal") or r.get("internal")),"created":r.get("Created") or r.get("CreatedAt") or r.get("created")})
    return sorted(out,key=lambda x:x["name"].lower())

def container_logs(cid):return engine_cli(["logs","--tail","250","--timestamps",_container_meta(cid)["id"]],30)

def _engine_prefix():
    if runtime()["engine"]=="podman":return [os.environ.get("ROGUEFORGE_PODMAN","/usr/bin/podman"),"--remote","--url",f"unix://{runtime()['socket']}"],os.environ.copy()
    e=os.environ.copy();e["DOCKER_HOST"]=f"unix://{runtime()['socket']}";return ["/usr/bin/docker"],e
def _popen_engine(args,stdin=False):
    pre,e=_engine_prefix();return subprocess.Popen(pre+args,env=e,stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
def _cleanup_terminals():
    now=time.time();stale=[]
    with _terminal_lock:
        for t,s in _terminal_sessions.items():
            if now-s["lastAccess"]>TERMINAL_TTL or (s.get("closed") and now-s["lastAccess"]>TERMINAL_CLOSED_GRACE):stale.append(t)
    for t in stale:close_terminal(t)
def _terminal_reader(token):
    s=_terminal_sessions.get(token)
    if not s:return
    p=s["process"]
    try:
        for line in iter(p.stdout.readline,""):
            with _terminal_lock:
                c=_terminal_sessions.get(token)
                if not c:break
                c["chunks"].append(line)
                if len(c["chunks"])>MAX_TERMINAL_CHUNKS:trim=len(c["chunks"])-MAX_TERMINAL_CHUNKS;del c["chunks"][:trim];c["baseCursor"]+=trim
    finally:
        with _terminal_lock:
            c=_terminal_sessions.get(token)
            if c:c["closed"]=True;c["exitCode"]=p.poll()
def start_terminal(cid):
    _cleanup_terminals();m=_container_meta(cid);ins=inspect_container(cid)
    if not ins.get("running"):raise RuntimeError("Container must be running before opening a terminal")
    shell="/bin/sh"
    try:
        q=engine_cli(["exec",m["id"],"sh","-lc","command -v bash || command -v sh"],30).strip().splitlines();shell=q[-1].strip() if q else shell
    except Exception:pass
    p=_popen_engine(["exec","-i",m["id"],shell],True);token=secrets.token_urlsafe(24);s={"token":token,"containerId":m["id"],"containerName":m["name"],"shell":shell,"process":p,"chunks":[],"baseCursor":0,"created":time.time(),"lastAccess":time.time(),"closed":False,"exitCode":None}
    with _terminal_lock:_terminal_sessions[token]=s
    threading.Thread(target=_terminal_reader,args=(token,),daemon=True).start();return {"ok":True,"token":token,"container":m["name"],"shell":shell,"cursor":0}
def terminal_output(token,cursor):
    _cleanup_terminals()
    with _terminal_lock:
        s=_terminal_sessions.get(token)
        if not s:raise FileNotFoundError("terminal session")
        s["lastAccess"]=time.time();start=max(0,cursor-s["baseCursor"]);return {"output":"".join(s["chunks"][start:]),"cursor":s["baseCursor"]+len(s["chunks"]),"closed":s["closed"],"exitCode":s["exitCode"],"container":s["containerName"],"shell":s["shell"]}
def terminal_input(token,value):
    if not isinstance(value,str) or len(value.encode())>8192:raise ValueError("terminal input is too large")
    with _terminal_lock:
        s=_terminal_sessions.get(token)
        if not s:raise FileNotFoundError("terminal session")
        s["lastAccess"]=time.time();p=s["process"]
    if p.poll() is not None or not p.stdin:raise RuntimeError("terminal session is closed")
    p.stdin.write(value);p.stdin.flush();return {"ok":True}
def close_terminal(token):
    with _terminal_lock:s=_terminal_sessions.pop(token,None)
    if not s:return {"ok":True}
    p=s["process"]
    try:
        if p.stdin:p.stdin.close()
    except Exception:pass
    if p.poll() is None:
        try:p.terminate();p.wait(timeout=2)
        except Exception:
            try:p.kill()
            except Exception:pass
    return {"ok":True}
def stream_logs(h,cid):
    p=_popen_engine(["logs","--follow","--tail","150","--timestamps",_container_meta(cid)["id"]]);h.send_response(200);h.send_header("content-type","text/event-stream");h.send_header("cache-control","no-cache, no-store");h.send_header("connection","keep-alive");h.send_header("x-accel-buffering","no");h.end_headers()
    try:
        h.wfile.write(b"event: ready\ndata: {}\n\n");h.wfile.flush()
        for line in iter(p.stdout.readline,""):h.wfile.write(b"data: "+json.dumps({"line":line.rstrip("\n")}).encode()+b"\n\n");h.wfile.flush()
    except (BrokenPipeError,ConnectionResetError):pass
    finally:
        if p.poll() is None:p.terminate()

def diagnostics():
    rt=runtime();return {"auth":auth_diagnostics(),"runtime":{"engine":rt["engine"],"socket":rt["socket"],"socketExists":Path(rt["socket"]).exists(),"context":rt.get("context")},"stacks":{"path":str(STACKS_DIR),"exists":STACKS_DIR.is_dir(),"readable":os.access(STACKS_DIR,os.R_OK),"selfStack":SELF_STACK},"discovery":discovery_diagnostics()}
class Handler(BaseHTTPRequestHandler):
    server_version=f"RogueForge/{VERSION}"
    def log_message(self,fmt,*args):sys.stderr.write("%s - %s\n"%(self.log_date_time_string(),fmt%args))
    def send_json(self,v,status=200,headers=None):
        raw=json.dumps(v,separators=(",",":")).encode();self.send_response(status);self.send_header("content-type","application/json");self.send_header("content-length",str(len(raw)));self.send_header("cache-control","no-store");self.send_header("x-content-type-options","nosniff");
        for n,c in (headers or {}).items():self.send_header(n,c)
        self.end_headers();self.wfile.write(raw)
    def session_payload(self):
        a=load_auth();cookie=SimpleCookie(self.headers.get("cookie",""));m=cookie.get("rogueforge_session");return read_session(m.value,a) if a and m else None
    def require_auth(self,csrf=False):
        if not load_auth():self.send_json({"error":"administrator account is not configured","auth":auth_diagnostics()},503);return None
        s=self.session_payload()
        if not s:self.send_json({"error":"authentication required"},401);return None
        if csrf and not hmac.compare_digest(self.headers.get("x-csrf-token",""),s.get("csrf","")):self.send_json({"error":"invalid security token"},403);return None
        return s
    def session_cookie(self,token,clear=False):
        p=[f"rogueforge_session={token}","Path=/","HttpOnly","SameSite=Strict","Max-Age=0" if clear else f"Max-Age={SESSION_TTL}"]
        if self.headers.get("x-forwarded-proto","").split(",",1)[0].strip().lower()=="https":p.append("Secure")
        return "; ".join(p)
    def read_json(self):
        n=int(self.headers.get("content-length","0") or 0)
        if n>MAX_BODY:raise ValueError("request body too large")
        return json.loads(self.rfile.read(n) or b"{}")
    def send_static(self,rel):
        rel="index.html" if rel in ("","/") else rel.lstrip("/");p=(STATIC_DIR/rel).resolve()
        if STATIC_DIR not in p.parents and p!=STATIC_DIR:self.send_error(404);return
        if not p.is_file():p=STATIC_DIR/"index.html"
        d=p.read_bytes();self.send_response(200);self.send_header("content-type",mimetypes.guess_type(str(p))[0] or "application/octet-stream");self.send_header("content-length",str(len(d)));self.send_header("cache-control","no-store, max-age=0");self.send_header("pragma","no-cache");self.send_header("x-content-type-options","nosniff");self.end_headers();self.wfile.write(d)
    def do_GET(self):
        try:
            u=urlparse(self.path);path=u.path
            if path=="/api/auth/session":a=load_auth();s=self.session_payload();self.send_json({"configured":bool(a),"authenticated":bool(s),"user":s.get("user") if s else None,"csrf":s.get("csrf") if s else None,"auth":auth_diagnostics()});return
            if path=="/api/status":rt=runtime();s=self.session_payload();self.send_json({"appVersion":VERSION,"engine":rt["engine"],"version":rt["version"],"apiVersion":rt["apiVersion"],"context":rt.get("context"),"demo":DEMO_MODE,"publicUrl":PUBLIC_URL,"authConfigured":bool(load_auth()),"socket":rt["socket"] if s else "Protected","stacksDir":str(STACKS_DIR) if s else "Protected","iconsDir":str(ICONS_DIR) if s else "Protected"});return
            if path=="/api/stacks":self.send_json(discover_stacks());return
            if path=="/api/containers":self.send_json(containers());return
            if path=="/api/images":
                if not self.require_auth():return
                self.send_json(resource_images());return
            if path=="/api/volumes":
                if not self.require_auth():return
                self.send_json(resource_volumes());return
            if path=="/api/networks":
                if not self.require_auth():return
                self.send_json(resource_networks());return
            if path=="/api/operations":
                if not self.require_auth():return
                self.send_json(operation_list());return
            m=re.fullmatch(r"/api/operations/([A-Za-z0-9_-]+)",path)
            if m:
                if not self.require_auth():return
                self.send_json(operation_get(m.group(1)));return
            if path=="/health":runtime();self.send_json({"ok":True,"version":VERSION});return
            if path in ("/api/diagnostics","/api/discovery"):
                if not self.require_auth():return
                self.send_json(diagnostics() if path.endswith("diagnostics") else discovery_diagnostics());return
            m=re.fullmatch(r"/api/stacks/([^/]+)/(compose|env)",path)
            if m:
                if not self.require_auth():return
                name,kind=m.groups();p=compose_file(safe_stack(name)) if kind=="compose" else None;self.send_json({"name":p.name,"content":p.read_text(encoding="utf-8")} if p else stack_env(name));return
            m=re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/(logs|inspect|image-status)",path)
            if m:
                if not self.require_auth():return
                cid,kind=m.groups();self.send_json({"logs":container_logs(cid)} if kind=="logs" else (inspect_container(cid) if kind=="inspect" else image_status(cid)));return
            if path=="/api/containers/stats":
                if not self.require_auth():return
                self.send_json(container_stats());return
            m=re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/logs/stream",path)
            if m:
                if not self.require_auth():return
                stream_logs(self,m.group(1));return
            m=re.fullmatch(r"/api/terminal/([A-Za-z0-9_-]+)",path)
            if m:
                if not self.require_auth():return
                try:cursor=max(0,int((parse_qs(u.query).get("cursor") or ["0"])[0]))
                except ValueError:cursor=0
                self.send_json(terminal_output(m.group(1),cursor));return
            self.send_static(path)
        except FileNotFoundError:self.send_json({"error":"not found"},404)
        except PermissionError as e:self.send_json({"error":str(e)},409)
        except Exception as e:self.send_json({"error":str(e)},500)
    def do_POST(self):
        try:
            path=urlparse(self.path).path
            if path=="/api/auth/login":
                client=self.client_address[0]
                if not login_allowed(client):self.send_json({"error":"too many login attempts; try again later"},429);return
                a=load_auth();payload=self.read_json();valid=bool(a) and hmac.compare_digest(str(payload.get("username","")),a["username"]) and verify_password(payload.get("password",""),a)
                if not valid:login_allowed(client,False);time.sleep(.35);self.send_json({"error":"invalid username or password"},401);return
                login_allowed(client,True);token,s=make_session(a);self.send_json({"ok":True,"user":s["user"],"csrf":s["csrf"]},headers={"set-cookie":self.session_cookie(token)});return
            if path=="/api/auth/logout":
                if not self.require_auth(csrf=True):return
                self.send_json({"ok":True},headers={"set-cookie":self.session_cookie("",True)});return
            if path=="/api/operations":
                if not self.require_auth(csrf=True):return
                p=self.read_json();self.send_json(start_operation(str(p.get("scope") or ""),str(p.get("target") or ""),str(p.get("action") or "")),202);return
            m=re.fullmatch(r"/api/stacks/([^/]+)/(start|stop|restart|pull|recreate|update)",path)
            if m:
                if not self.require_auth(csrf=True):return
                n,a=m.groups();self.send_json(update_stack(n) if a=="update" else run_stack_action(n,a));return
            if path=="/api/containers/update-all":
                if not self.require_auth(csrf=True):return
                ids=[x["id"] for x in containers() if not x.get("selfProtected")];self.send_json(bulk_container_action(ids,"update") if ids else {"ok":True,"action":"update","results":[]});return
            if path=="/api/containers/bulk":
                if not self.require_auth(csrf=True):return
                p=self.read_json();self.send_json(bulk_container_action(p.get("ids"),str(p.get("action") or "")));return
            m=re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/(start|stop|restart|update|recreate|remove|check-update)",path)
            if m:
                if not self.require_auth(csrf=True):return
                self.send_json(container_action(*m.groups()));return
            m=re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/terminal",path)
            if m:
                if not self.require_auth(csrf=True):return
                self.send_json(start_terminal(m.group(1)));return
            m=re.fullmatch(r"/api/terminal/([A-Za-z0-9_-]+)/input",path)
            if m:
                if not self.require_auth(csrf=True):return
                self.send_json(terminal_input(m.group(1),self.read_json().get("input","")));return
            self.send_json({"error":"not found"},404)
        except PermissionError as e:self.send_json({"error":str(e)},409)
        except Exception as e:self.send_json({"error":str(e)},500)
    def do_PUT(self):
        try:
            if not self.require_auth(csrf=True):return
            path=urlparse(self.path).path;m=re.fullmatch(r"/api/stacks/([^/]+)/(compose|env)",path)
            if not m:self.send_json({"error":"not found"},404);return
            name,kind=m.groups();content=self.read_json().get("content")
            if kind=="env":self.send_json(save_stack_env(name,content));return
            p=compose_file(safe_stack(name))
            if not p:raise FileNotFoundError("compose")
            if not isinstance(content,str) or len(content.encode())>1_000_000:raise ValueError("invalid compose content")
            backup=p.with_suffix(p.suffix+f".rogueforge-{int(time.time())}.bak");backup.write_bytes(p.read_bytes());p.write_text(content,encoding="utf-8")
            try:validate_stack(name)
            except Exception:p.write_bytes(backup.read_bytes());raise
            self.send_json({"ok":True,"backup":backup.name})
        except Exception as e:self.send_json({"error":str(e)},500)
    def do_DELETE(self):
        try:
            path=urlparse(self.path).path
            m=re.fullmatch(r"/api/operations/([A-Za-z0-9_-]+)",path)
            if m:
                if not self.require_auth(csrf=True):return
                self.send_json(cancel_operation(m.group(1)));return
            m=re.fullmatch(r"/api/terminal/([A-Za-z0-9_-]+)",path)
            if not m:self.send_json({"error":"not found"},404);return
            if not self.require_auth(csrf=True):return
            self.send_json(close_terminal(m.group(1)))
        except Exception as e:self.send_json({"error":str(e)},500)

def main():
    rt=runtime();a=auth_diagnostics()
    if not a["valid"]:sys.stderr.write(f"WARNING: authentication is not ready: {a}\n")
    srv=ThreadingHTTPServer((BIND,PORT),Handler);print(f"RogueForge {VERSION} listening on http://{BIND}:{PORT} ({rt['engine']}, {rt.get('context')})")
    try:srv.serve_forever()
    except KeyboardInterrupt:pass
    finally:srv.server_close()
if __name__=="__main__":main()
