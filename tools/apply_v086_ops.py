#!/usr/bin/env python3
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
