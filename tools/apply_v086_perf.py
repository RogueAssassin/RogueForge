#!/usr/bin/env python3
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

# BrokenPipeError is a normal client/proxy disconnect. Do not attempt to write a second
# error response to an already closed socket.
old='''    def send_json(self,payload,status=200,headers=None):
        raw=json.dumps(payload,separators=(",",":"),default=str).encode();self.send_response(status);self.send_header("content-type","application/json");self.send_header("content-length",str(len(raw)));self.send_header("cache-control","no-store");self.send_header("x-content-type-options","nosniff")
        for k,v in (headers or {}).items():self.send_header(k,v)
        self.end_headers();self.wfile.write(raw)'''
new='''    def send_json(self,payload,status=200,headers=None):
        raw=json.dumps(payload,separators=(",",":"),default=str).encode()
        try:
            self.send_response(status);self.send_header("content-type","application/json");self.send_header("content-length",str(len(raw)));self.send_header("cache-control","no-store");self.send_header("x-content-type-options","nosniff")
            for k,v in (headers or {}).items():self.send_header(k,v)
            self.end_headers();self.wfile.write(raw)
        except (BrokenPipeError,ConnectionResetError):return'''
replace(old,new)

# Add HEAD support for proxies/monitors. Keep it deliberately lightweight.
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

# Do not convert client disconnects into 500 responses from top-level handlers.
s=s.replace('except Exception as e:self.send_json({"error":str(e)},500)','except (BrokenPipeError,ConnectionResetError):return\n        except Exception as e:self.send_json({"error":str(e)},500)')

p.write_text(s,encoding='utf-8')
print('Applied RogueForge v0.8.6 performance and HTTP fixes')
