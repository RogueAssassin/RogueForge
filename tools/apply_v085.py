#!/usr/bin/env python3
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
