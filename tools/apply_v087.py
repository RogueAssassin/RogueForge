#!/usr/bin/env python3
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
