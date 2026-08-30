#!/usr/bin/env python3
"""Canonical RogueForge runtime preparation pipeline.

This single build tool replaces the historical per-version patch scripts. CI runs it
once before validation and publishing so release preparation has one deterministic path.
Do not add new version-named patch files; extend this pipeline until the patched runtime
is fully folded into the canonical source.
"""


# ---- migrated release-preparation stage 1 ----
from pathlib import Path

p=Path('rogueforge.py')
s=p.read_text(encoding='utf-8')

def replace(old,new):
    global s
    if old not in s:
        raise SystemExit('expected runtime block not found: '+old[:80])
    s=s.replace(old,new,1)

replace('"""RogueForge 0.8.2 — single-file Docker/Podman Compose operations runtime."""','"""RogueForge 0.8.5 — single-file Docker/Podman Compose operations runtime."""')
replace('VERSION="0.8.2"','VERSION="0.8.5"')
replace('EXCLUDED_DIRS={".git",".cache","node_modules","__pycache__","backup","backups"};','EXCLUDED_DIRS={".git",".cache","node_modules","__pycache__","backup","backups","update-backups","rogueforge-update-backups"};')

old='''    items=list(records.values()); used=set()\n    for r in items:\n        base=_norm(r.get("project") or r["key"]); key=base; i=2\n        while key in used:key=f"{base}-{i}"[:127];i+=1\n        r["key"]=key;used.add(key)'''
new='''    # Active Compose labels are authoritative. A recursive scan may discover old,\n    # alternate or backup Compose definitions for the same project; suppress those\n    # duplicates while retaining genuinely stopped projects that have no active label.\n    labelled_projects={str(r.get("project")) for r in records.values() if r.get("source")=="labels" and r.get("project")}\n    labelled_dirs={str(r["directory"]) for r in records.values() if r.get("source")=="labels"}\n    items=[]\n    seen_scan_projects=set()\n    for r in records.values():\n        if r.get("source")=="labels":items.append(r);continue\n        inferred=_norm(r["directory"].name)\n        if inferred in {_norm(x) for x in labelled_projects}:continue\n        if str(r["directory"]) in labelled_dirs:continue\n        if inferred in seen_scan_projects:continue\n        seen_scan_projects.add(inferred);items.append(r)\n    used=set()\n    for r in items:\n        base=_norm(r.get("project") or r["key"]); key=base; i=2\n        while key in used:key=f"{base}-{i}"[:127];i+=1\n        r["key"]=key;used.add(key)'''
replace(old,new)

old='''def save_stack_env(name,content):\n    if not isinstance(content,str) or len(content.encode())>1_000_000:raise ValueError("invalid environment content")\n    p=safe_stack(name)/".env";backup=None\n    if p.is_file():backup=p.with_name(f".env.rogueforge-{int(time.time())}.bak");backup.write_bytes(p.read_bytes())\n    p.write_text(content,encoding="utf-8")\n    try:validate_stack(name)\n    except Exception:\n        if backup and backup.is_file():p.write_bytes(backup.read_bytes())\n        else:p.unlink(missing_ok=True)\n        raise\n    return {"ok":True,"backup":backup.name if backup else None}'''
new='''def _backup_file(source,kind):\n    root=Path(os.environ.get("ROGUEFORGE_BACKUP_TMP",os.environ.get("TMPDIR","/tmp")))/"rogueforge"/kind\n    root.mkdir(parents=True,exist_ok=True)\n    target=root/f"{_norm(source.parent.name)}-{int(time.time()*1000)}-{source.name}.bak"\n    target.write_bytes(source.read_bytes());return target\ndef save_stack_env(name,content):\n    if not isinstance(content,str) or len(content.encode())>1_000_000:raise ValueError("invalid environment content")\n    p=safe_stack(name)/".env";backup=_backup_file(p,"env-backups") if p.is_file() else None\n    p.write_text(content,encoding="utf-8")\n    try:validate_stack(name)\n    except Exception:\n        if backup and backup.is_file():p.write_bytes(backup.read_bytes())\n        else:p.unlink(missing_ok=True)\n        raise\n    return {"ok":True,"backup":str(backup) if backup else None}'''
replace(old,new)

start=s.index('def container_stats():')
end=s.index('def image_status(',start)
s=s[:start]+'''def container_stats():\n    try:\n        raw=engine_cli(["stats","--no-stream","--format","json"],60).strip();rows=[]\n        if not raw:return {}\n        try:\n            parsed=json.loads(raw);rows=parsed if isinstance(parsed,list) else [parsed]\n        except Exception:\n            for line in raw.splitlines():\n                try:\n                    parsed=json.loads(line);rows.extend(parsed if isinstance(parsed,list) else [parsed])\n                except Exception:pass\n        result={}\n        for r in rows:\n            if not isinstance(r,dict):continue\n            cid=str(r.get("id") or r.get("ID") or r.get("ContainerID") or r.get("Container") or "")\n            name=str(r.get("name") or r.get("Name") or r.get("ContainerName") or "").lstrip("/")\n            value={"cpu":r.get("cpu_percent") or r.get("CPUPerc") or r.get("CPU") or r.get("CPU %"),"memory":r.get("mem_usage") or r.get("MemUsage") or r.get("MEM USAGE / LIMIT") or r.get("Memory"),"memoryPercent":r.get("mem_percent") or r.get("MemPerc") or r.get("MEM %"),"network":r.get("net_io") or r.get("NetIO") or r.get("NET I/O"),"block":r.get("block_io") or r.get("BlockIO") or r.get("BLOCK I/O"),"pids":r.get("pids") or r.get("PIDs")}\n            if cid:result[cid[:12]]=value\n            if name:result[name]=value\n        return result\n    except Exception as e:\n        sys.stderr.write(f"container stats failed: {e}\\n");return {}\n'''+s[end:]

old='''    if action=="update":\n        if not m["composeManaged"]:return {"ok":True,"output":engine_cli(["pull",m["image"]],900),"recreated":False,"message":"Image pulled; standalone container not automatically recreated."}\n        return {"ok":True,"output":(run_compose(m["project"],["pull",m["service"]])+"\\n"+run_compose(m["project"],["up","-d","--no-deps","--remove-orphans",m["service"]]))[-100000:],"recreated":True}'''
new='''    if action=="update":\n        pulled=engine_cli(["pull",m["image"]],900)\n        if not m["composeManaged"]:return {"ok":True,"output":pulled,"recreated":False,"message":"Image pulled; standalone container not automatically recreated."}\n        recreated=run_compose(m["project"],["up","-d","--no-deps",m["service"]])\n        return {"ok":True,"output":(pulled+"\\n"+recreated)[-100000:],"recreated":True}'''
replace(old,new)

old='''            backup=p.with_suffix(p.suffix+f".rogueforge-{int(time.time())}.bak");backup.write_bytes(p.read_bytes());p.write_text(content,encoding="utf-8")\n            try:validate_stack(name)\n            except Exception:p.write_bytes(backup.read_bytes());raise\n            self.send_json({"ok":True,"backup":backup.name})'''
new='''            backup=_backup_file(p,"compose-backups");p.write_text(content,encoding="utf-8")\n            try:validate_stack(name)\n            except Exception:p.write_bytes(backup.read_bytes());raise\n            self.send_json({"ok":True,"backup":str(backup)})'''
replace(old,new)

p.write_text(s,encoding='utf-8')
print('Applied RogueForge v0.8.5 runtime fixes')

# ---- migrated release-preparation stage 2 ----
from pathlib import Path

p=Path('rogueforge.py')
s=p.read_text(encoding='utf-8')

def replace(old,new):
    global s
    if old not in s:
        raise SystemExit('expected v0.8.6 runtime block not found: '+old[:100])
    s=s.replace(old,new,1)

replace('"""RogueForge 0.8.5 — single-file Docker/Podman Compose operations runtime."""','"""RogueForge 0.8.6 — single-file Docker/Podman Compose operations runtime."""')
replace('VERSION="0.8.5"','VERSION="0.8.6"')

replace(
'STACKS_DIR=Path(os.environ.get("ROGUEFORGE_STACKS_DIR","/opt/media-server")).resolve(); STATIC_DIR=Path(os.environ.get("ROGUEFORGE_STATIC_DIR",Path(__file__).with_name("static"))).resolve()',
'''MEDIA_ROOT=Path(os.environ.get("ROGUEFORGE_MEDIA_ROOT","/opt/media-server")).resolve()
COMPOSE_ROOT=Path(os.environ.get("ROGUEFORGE_COMPOSE_ROOT",os.environ.get("ROGUEFORGE_STACKS_DIR",str(MEDIA_ROOT)))).resolve()
ENV_ROOT=Path(os.environ.get("ROGUEFORGE_ENV_ROOT",str(COMPOSE_ROOT))).resolve()
# STACKS_DIR remains as a compatibility alias for older UI/API code.
STACKS_DIR=COMPOSE_ROOT
STATIC_DIR=Path(os.environ.get("ROGUEFORGE_STATIC_DIR",Path(__file__).with_name("static"))).resolve()''')

replace(
'''def stack_env(name):
    p=safe_stack(name)/".env";return {"name":".env","exists":p.is_file(),"content":p.read_text(encoding="utf-8") if p.is_file() else ""}''',
'''def stack_env_path(name):
    d=safe_stack(name)
    try:rel=d.resolve().relative_to(COMPOSE_ROOT)
    except ValueError:rel=Path(d.name)
    return (ENV_ROOT/rel/".env").resolve()
def stack_env(name):
    p=stack_env_path(name);return {"name":".env","path":str(p),"exists":p.is_file(),"content":p.read_text(encoding="utf-8") if p.is_file() else ""}''')
replace('p=safe_stack(name)/".env";backup=_backup_file(p,"env-backups") if p.is_file() else None','p=stack_env_path(name);p.parent.mkdir(parents=True,exist_ok=True);backup=_backup_file(p,"env-backups") if p.is_file() else None')

old_compose='''def compose_command(stack,args):
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
    return d,cmd+args,env'''
new_compose='''def compose_command(stack,args):
    d=safe_stack(stack);cf=compose_file(d)
    if not cf:raise RuntimeError("compose file not found")
    rt=runtime();env=os.environ.copy();ef=stack_env_path(stack)
    if rt["engine"]=="podman":
        if PODMAN_REMOTE:env=podman_remote_env()
        env["PODMAN_COMPOSE_WARNING_LOGS"]="false";env["PODMAN_COMPOSE_IN_POD"]="false"
        # The bundled Podman client can be older than the host daemon and may reject
        # modern `podman compose --env-file` wrapper flags. Invoke podman-compose
        # directly and inject the stack .env values into its process environment.
        if ef.is_file():
            for line in ef.read_text(encoding="utf-8",errors="replace").splitlines():
                line=line.strip()
                if not line or line.startswith("#") or "=" not in line:continue
                key,value=line.split("=",1);key=key.strip()
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$",key):
                    value=value.strip()
                    if len(value)>=2 and value[0]==value[-1] and value[0] in ("'",'"'):value=value[1:-1]
                    env[key]=value
        cmd=[os.environ.get("ROGUEFORGE_PODMAN_COMPOSE","/usr/bin/podman-compose"),"-f",str(cf)]
    else:
        env["DOCKER_HOST"]=f"unix://{rt['socket']}";cmd=["/usr/bin/docker","compose"]
        if ef.is_file():cmd += ["--env-file",str(ef)]
        cmd += ["-f",str(cf)]
    return d,cmd+args,env'''
replace(old_compose,new_compose)

replace(
'''def diagnostics():
    rt=runtime();return {"auth":auth_diagnostics(),"runtime":{"engine":rt["engine"],"socket":rt["socket"],"socketExists":Path(rt["socket"]).exists(),"context":rt.get("context")},"stacks":{"path":str(STACKS_DIR),"exists":STACKS_DIR.is_dir(),"readable":os.access(STACKS_DIR,os.R_OK),"selfStack":SELF_STACK},"discovery":discovery_diagnostics()}''',
'''def diagnostics():
    rt=runtime();return {"auth":auth_diagnostics(),"runtime":{"engine":rt["engine"],"socket":rt["socket"],"socketExists":Path(rt["socket"]).exists(),"context":rt.get("context")},"paths":{"mediaRoot":str(MEDIA_ROOT),"composeRoot":str(COMPOSE_ROOT),"envRoot":str(ENV_ROOT)},"stacks":{"path":str(COMPOSE_ROOT),"exists":COMPOSE_ROOT.is_dir(),"readable":os.access(COMPOSE_ROOT,os.R_OK),"selfStack":SELF_STACK},"discovery":discovery_diagnostics()}''')

replace(
'''if path=="/api/status":rt=runtime();s=self.session_payload();self.send_json({"appVersion":VERSION,"engine":rt["engine"],"version":rt["version"],"apiVersion":rt["apiVersion"],"context":rt.get("context"),"demo":DEMO_MODE,"publicUrl":PUBLIC_URL,"authConfigured":bool(load_auth()),"socket":rt["socket"] if s else "Protected","stacksDir":str(STACKS_DIR) if s else "Protected","iconsDir":str(ICONS_DIR) if s else "Protected"});return''',
'''if path=="/api/status":rt=runtime();s=self.session_payload();self.send_json({"appVersion":VERSION,"engine":rt["engine"],"version":rt["version"],"apiVersion":rt["apiVersion"],"context":rt.get("context"),"demo":DEMO_MODE,"publicUrl":PUBLIC_URL,"authConfigured":bool(load_auth()),"socket":rt["socket"] if s else "Protected","stacksDir":str(COMPOSE_ROOT) if s else "Protected","composeRoot":str(COMPOSE_ROOT) if s else "Protected","envRoot":str(ENV_ROOT) if s else "Protected","mediaRoot":str(MEDIA_ROOT) if s else "Protected","iconsDir":str(ICONS_DIR) if s else "Protected"});return''')

old='''    if action=="update":
        pulled=engine_cli(["pull",m["image"]],900)
        if not m["composeManaged"]:return {"ok":True,"output":pulled,"recreated":False,"message":"Image pulled; standalone container not automatically recreated."}
        recreated=run_compose(m["project"],["up","-d","--no-deps",m["service"]])
        return {"ok":True,"output":(pulled+"\\n"+recreated)[-100000:],"recreated":True}'''
new='''    if action=="update":
        before=inspect_container(cid).get("imageId")
        pulled=engine_cli(["pull",m["image"]],900)
        try:
            raw=json.loads(engine_cli(["image","inspect",m["image"]],60) or "[]");obj=raw[0] if isinstance(raw,list) and raw else raw;expected=obj.get("Id") or obj.get("ID")
        except Exception:expected=None
        if not m["composeManaged"]:return {"ok":True,"output":pulled,"recreated":False,"message":"Image pulled; standalone container not automatically recreated.","beforeImageId":before,"pulledImageId":expected}
        if expected and before==expected:return {"ok":True,"output":pulled,"recreated":False,"message":"Container is already using the current image.","beforeImageId":before,"pulledImageId":expected,"runningImageId":before,"verified":True}
        if runtime()["engine"]=="podman":
            old_name=m["name"];preserved=f"{old_name}-rogueforge-old-{int(time.time())}"
            engine_cli(["stop","--time","10",m["id"]],60)
            engine_cli(["rename",m["id"],preserved],60)
            try:
                recreated=run_compose(m["project"],["up","-d",m["service"]])
                inspected=json.loads(engine_cli(["inspect",old_name],60) or "[]");obj=inspected[0] if isinstance(inspected,list) and inspected else inspected;running=obj.get("Image")
                if expected and running!=expected:raise RuntimeError(f"Update verification failed: expected image {expected}, running {running}")
                engine_cli(["rm","-f",preserved],60)
                return {"ok":True,"output":(pulled+"\\n"+recreated)[-100000:],"recreated":True,"beforeImageId":before,"pulledImageId":expected,"runningImageId":running,"verified":bool(expected and running==expected)}
            except Exception:
                try:engine_cli(["rm","-f",old_name],60)
                except Exception:pass
                try:engine_cli(["rename",preserved,old_name],60);engine_cli(["start",old_name],60)
                except Exception:pass
                raise
        recreated=run_compose(m["project"],["up","-d","--no-deps","--force-recreate",m["service"]])
        try:
            inspected=json.loads(engine_cli(["inspect",m["name"]],60) or "[]");obj=inspected[0] if isinstance(inspected,list) and inspected else inspected;running=obj.get("Image")
        except Exception:running=None
        if expected and running!=expected:raise RuntimeError(f"Update verification failed: expected image {expected}, running {running}")
        return {"ok":True,"output":(pulled+"\\n"+recreated)[-100000:],"recreated":True,"beforeImageId":before,"pulledImageId":expected,"runningImageId":running,"verified":bool(expected and running==expected)}'''
replace(old,new)

p.write_text(s,encoding='utf-8')
print('Applied RogueForge v0.8.6 runtime fixes')

# ---- migrated release-preparation stage 3 ----
from pathlib import Path

p=Path('rogueforge.py')
s=p.read_text(encoding='utf-8')

def replace(old,new):
    global s
    if old not in s:
        raise SystemExit('expected performance block not found: '+old[:120])
    s=s.replace(old,new,1)

old='''def containers():
    result=[]
    for x in load_containers() or []:
        fid=str(x.get("Id") or x.get("ID") or x.get("id") or "")
        try:m=_container_meta(fid[:12]); state=str(x.get("State") or x.get("state") or "unknown").lower();result.append({"id":fid[:12],"name":m["name"],"image":m["image"],"state":state,"status":x.get("Status") or x.get("status") or state,"ports":x.get("Ports") or x.get("ports") or [],"project":m["project"],"service":m["service"] or None,"composeManaged":m["composeManaged"],"selfProtected":m["selfProtected"]})
        except Exception:pass
    return sorted(result,key=lambda i:(i["state"]!="running",i["name"].lower()))'''
new='''def containers(inventory=None,registry=None):
    # Use one immutable runtime inventory snapshot for the whole response. The older
    # implementation called load_containers() again from _container_meta() for every
    # container, producing N+1 remote Podman calls and proxy/browser timeouts.
    inventory=list(inventory if inventory is not None else (load_containers() or []))
    registry=registry or _build_registry()
    result=[]
    for x in inventory:
        try:
            fid=str(x.get("Id") or x.get("ID") or x.get("id") or "")
            labels=x.get("Labels") or x.get("labels") or {}; labels=labels if isinstance(labels,dict) else {}
            names=x.get("Names") or x.get("names") or []; names=[names] if isinstance(names,str) else names
            name=names[0].lstrip("/") if names else str(x.get("Name") or x.get("name") or "unnamed")
            project=str(labels.get("com.docker.compose.project") or labels.get("io.podman.compose.project") or "standalone")
            service=str(labels.get("com.docker.compose.service") or labels.get("io.podman.compose.service") or "")
            image=x.get("Image") or x.get("ImageName") or x.get("image") or "unknown"
            rec=None
            if project!="standalone":rec=registry["aliases"].get(project) or registry["aliases"].get(_norm(project))
            project_key=rec["key"] if rec else project
            state=str(x.get("State") or x.get("state") or "unknown").lower()
            result.append({"id":fid[:12],"name":name,"image":image,"state":state,"status":x.get("Status") or x.get("status") or state,"ports":x.get("Ports") or x.get("ports") or [],"project":project_key,"service":service or None,"composeManaged":bool(service and project!="standalone"),"selfProtected":name==SELF_STACK or project==SELF_STACK})
        except Exception as e:sys.stderr.write(f"container inventory row skipped: {e}\\n")
    return sorted(result,key=lambda i:(i["state"]!="running",i["name"].lower()))'''
replace(old,new)

old='''def discover_stacks():
    reg=_build_registry(force=True); members={}
    for c in containers():members.setdefault(c.get("project","standalone"),[]).append(c)'''
new='''def discover_stacks():
    reg=_build_registry(force=True); members={}
    # Registry construction performs one inventory request. containers() then performs
    # one additional snapshot only, rather than one request per container.
    for c in containers(registry=reg):members.setdefault(c.get("project","standalone"),[]).append(c)'''
replace(old,new)

old='''    def send_json(self,v,status=200,headers=None):
        raw=json.dumps(v,separators=(",",":")).encode();self.send_response(status);self.send_header("content-type","application/json");self.send_header("content-length",str(len(raw)));self.send_header("cache-control","no-store");self.send_header("x-content-type-options","nosniff");
        for n,c in (headers or {}).items():self.send_header(n,c)
        self.end_headers();self.wfile.write(raw)'''
new='''    def send_json(self,v,status=200,headers=None):
        raw=json.dumps(v,separators=(",",":")).encode()
        try:
            self.send_response(status);self.send_header("content-type","application/json");self.send_header("content-length",str(len(raw)));self.send_header("cache-control","no-store");self.send_header("x-content-type-options","nosniff")
            for n,c in (headers or {}).items():self.send_header(n,c)
            self.end_headers();self.wfile.write(raw)
        except (BrokenPipeError,ConnectionResetError):return'''
replace(old,new)

needle='''    def do_GET(self):
        try:'''
replacement='''    def do_HEAD(self):
        path=urlparse(self.path).path
        if path in ("/","/health") or path.startswith("/static/"):
            self.send_response(200);self.send_header("cache-control","no-store");self.end_headers();return
        self.send_response(404);self.end_headers()
    def do_GET(self):
        try:'''
replace(needle,replacement)

s=s.replace('except Exception as e:self.send_json({"error":str(e)},500)','except (BrokenPipeError,ConnectionResetError):return\n        except Exception as e:self.send_json({"error":str(e)},500)')

p.write_text(s,encoding='utf-8')
print('Applied RogueForge v0.8.6 performance and HTTP fixes')

# ---- migrated release-preparation stage 4 ----
from pathlib import Path

p=Path('rogueforge.py')
s=p.read_text(encoding='utf-8')

def replace(old,new):
    global s
    if old not in s:
        raise SystemExit('expected v0.8.6 ops block not found: '+old[:140])
    s=s.replace(old,new,1)

# Add a short shared inventory cache. Overview, Stacks and Runtime are loaded together,
# so multiple HTTP requests should share the same Podman inventory snapshot.
replace(
'_terminal_sessions={}; _terminal_lock=threading.Lock(); TERMINAL_TTL=1800; TERMINAL_CLOSED_GRACE=60; MAX_TERMINAL_CHUNKS=2500',
'''_terminal_sessions={}; _terminal_lock=threading.Lock(); TERMINAL_TTL=1800; TERMINAL_CLOSED_GRACE=60; MAX_TERMINAL_CHUNKS=2500
INVENTORY_CACHE_SECONDS=max(1,min(30,int(os.environ.get("ROGUEFORGE_INVENTORY_CACHE","2"))))
_inventory_cache={"time":0.0,"items":[]}; _inventory_lock=threading.Lock()''')

replace('def load_containers():\n','def _load_containers_uncached():\n')
replace(
'def _raw_container(cid):',
'''def load_containers(force=False):
    now=time.monotonic()
    with _inventory_lock:
        if not force and _inventory_cache["items"] and now-_inventory_cache["time"]<INVENTORY_CACHE_SECONDS:
            return list(_inventory_cache["items"])
    items=list(_load_containers_uncached() or [])
    with _inventory_lock:
        _inventory_cache["time"]=now;_inventory_cache["items"]=items
    return list(items)
def invalidate_inventory():
    with _inventory_lock:_inventory_cache["time"]=0.0;_inventory_cache["items"]=[]
    invalidate_resource_cache()
def _raw_container(cid):''')

# The registry already has its own cache. Do not force a filesystem/label rebuild on
# every browser request; diagnostics remains the explicit force-refresh path.
replace('def discover_stacks():\n    reg=_build_registry(force=True); members={}',
        'def discover_stacks():\n    reg=_build_registry(); members={}')

# Match the proven media-server compose_for lifecycle: down/up is deterministic with
# Podman Compose 1.5.0 and avoids stale named containers surviving stop/recreate flows.
replace(
'''def run_stack_action(stack,action):
    m={"start":["up","-d"],"stop":["stop"],"restart":["restart"],"pull":["pull"],"recreate":["up","-d","--force-recreate"]}
    if action not in m:raise ValueError("unsupported action")
    safe_stack(stack);return {"ok":True,"output":run_compose(stack,m[action])}
def update_stack(name):return {"ok":True,"output":(run_compose(name,["pull"])+"\\n"+run_compose(name,["up","-d","--remove-orphans"]))[-100000:]}''',
'''def run_stack_action(stack,action):
    safe_stack(stack)
    if action=="start":out=run_compose(stack,["up","-d"])
    elif action=="stop":out=run_compose(stack,["down"])
    elif action=="restart":out=run_compose(stack,["down"])+"\\n"+run_compose(stack,["up","-d"])
    elif action=="pull":out=run_compose(stack,["pull"])
    elif action=="recreate":out=run_compose(stack,["down"])+"\\n"+run_compose(stack,["up","-d"])
    else:raise ValueError("unsupported action")
    invalidate_inventory();_discovery_cache["time"]=0.0
    return {"ok":True,"output":out[-100000:]}
def update_stack(name):
    safe_stack(name)
    # Pull the whole stack, then use the same deterministic down/up sequence as the
    # host media-server compose_for helper. This favors correctness over zero downtime.
    out=run_compose(name,["pull"])+"\\n"+run_compose(name,["down"])+"\\n"+run_compose(name,["up","-d"])
    invalidate_inventory();_discovery_cache["time"]=0.0
    return {"ok":True,"output":out[-100000:]}''')

p.write_text(s,encoding='utf-8')
print('Applied RogueForge v0.8.6 inventory cache and media-server lifecycle fixes')

# ---- migrated release-preparation stage 5 ----
from pathlib import Path

p=Path('rogueforge.py')
s=p.read_text(encoding='utf-8')
needle='''            if path=="/api/stacks":self.send_json(discover_stacks());return
            if path=="/api/containers":self.send_json(containers());return'''
replacement='''            if path=="/api/dashboard":
                # One browser request for the initial dashboard. The short shared
                # inventory/discovery caches ensure stacks and containers reuse the
                # same Podman snapshot instead of multiplying engine round-trips.
                rt=runtime();session=self.session_payload()
                self.send_json({"status":{"appVersion":VERSION,"engine":rt["engine"],"version":rt["version"],"apiVersion":rt["apiVersion"],"context":rt.get("context"),"demo":DEMO_MODE,"publicUrl":PUBLIC_URL,"authConfigured":bool(load_auth()),"socket":rt["socket"] if session else "Protected","stacksDir":str(STACKS_DIR) if session else "Protected","composeRoot":str(COMPOSE_ROOT) if session else "Protected","envRoot":str(ENV_ROOT) if session else "Protected","mediaRoot":str(MEDIA_ROOT) if session else "Protected","iconsDir":str(ICONS_DIR) if session else "Protected"},"stacks":discover_stacks(),"containers":containers(),"auth":{"configured":bool(load_auth()),"authenticated":bool(session),"user":session.get("user") if session else None,"csrf":session.get("csrf") if session else None,"auth":auth_diagnostics()}});return
            if path=="/api/stacks":self.send_json(discover_stacks());return
            if path=="/api/containers":self.send_json(containers());return'''
if needle not in s: raise SystemExit('dashboard route insertion point not found')
s=s.replace(needle,replacement,1)
p.write_text(s,encoding='utf-8')

app=Path('static/app.js')
a=app.read_text(encoding='utf-8')
old='''    [state.status, state.stacks, state.containers, state.auth] = await Promise.all([api("/api/status"), api("/api/stacks"), api("/api/containers"), api("/api/auth/session")]);'''
new='''    const snapshot = await api("/api/dashboard");
    state.status = snapshot.status;
    state.stacks = snapshot.stacks || [];
    state.containers = snapshot.containers || [];
    state.auth = snapshot.auth || state.auth;'''
if old not in a: raise SystemExit('frontend load block not found')
a=a.replace(old,new,1)
app.write_text(a,encoding='utf-8')
print('Applied RogueForge v0.8.7 unified dashboard snapshot')

# ---- migrated release-preparation stage 6 ----
from pathlib import Path

app=Path('static/app.js')
s=app.read_text(encoding='utf-8')

def replace(old,new):
    global s
    if old not in s:
        raise SystemExit('expected v0.8.7 async block not found: '+old[:140])
    s=s.replace(old,new,1)

replace(
'const state = { status: null, stacks: [], containers: [], currentStack: null, loading: false, auth: { configured: false, authenticated: false, user: null, csrf: null } };',
'''const state = { status: null, stacks: [], containers: [], currentStack: null, loading: false, auth: { configured: false, authenticated: false, user: null, csrf: null }, hydrated: false, lastRefresh: 0 };
const DASHBOARD_CACHE_KEY = "rogueforge.dashboard.snapshot.v1";
function saveDashboardSnapshot(snapshot){
  try { sessionStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify({ savedAt: Date.now(), snapshot })); } catch {}
}
function hydrateDashboardSnapshot(){
  try {
    const cached=JSON.parse(sessionStorage.getItem(DASHBOARD_CACHE_KEY)||"null");
    if(!cached?.snapshot || Date.now()-Number(cached.savedAt||0)>60000) return false;
    state.status=cached.snapshot.status||state.status;
    state.stacks=cached.snapshot.stacks||[];
    state.containers=cached.snapshot.containers||[];
    state.auth=cached.snapshot.auth||state.auth;
    if(state.status){state.hydrated=true;renderAll();renderAuth();return true;}
  } catch {}
  return false;
}''')

replace(
'''    const snapshot = await api("/api/dashboard");
    state.status = snapshot.status;
    state.stacks = snapshot.stacks || [];
    state.containers = snapshot.containers || [];
    state.auth = snapshot.auth || state.auth;
    renderAll();''',
'''    const snapshot = await api("/api/dashboard");
    state.status = snapshot.status;
    state.stacks = snapshot.stacks || [];
    state.containers = snapshot.containers || [];
    state.auth = snapshot.auth || state.auth;
    state.hydrated = true;
    state.lastRefresh = Date.now();
    saveDashboardSnapshot(snapshot);
    renderAll();''')

replace(
'''setView(pageMeta[location.hash.slice(1)] ? location.hash.slice(1) : "overview");
load({ quiet: true });
setInterval(() => load({ quiet: true }), 15000);''',
'''setView(pageMeta[location.hash.slice(1)] ? location.hash.slice(1) : "overview");
hydrateDashboardSnapshot();
load({ quiet: true });
// Runtime inventory refreshes independently of CPU/RAM stats. Slow stats collection in
// container-controls.js must never block the main dashboard from becoming interactive.
setInterval(() => { if(!document.hidden) load({ quiet: true }); }, 10000);
document.addEventListener("visibilitychange", () => {
  if(!document.hidden && Date.now()-state.lastRefresh>5000) load({ quiet: true });
});''')

app.write_text(s,encoding='utf-8')
print('Applied RogueForge v0.8.7 instant hydration and non-blocking refresh')
