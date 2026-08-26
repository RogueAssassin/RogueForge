#!/usr/bin/env python3
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
