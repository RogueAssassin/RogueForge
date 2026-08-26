#!/usr/bin/env python3
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
        # Mirror the proven host media-server helper: podman compose --env-file ... -f ...
        cmd=[os.environ.get("ROGUEFORGE_PODMAN","/usr/bin/podman"),"compose"]
        if ef.is_file():cmd += ["--env-file",str(ef)]
        cmd += ["-f",str(cf)]
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
