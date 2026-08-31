const $ = selector => document.querySelector(selector);
const setText = (selector, value) => { const node=$(selector); if(node) node.textContent=value == null ? "—" : String(value); return node; };
const setHtml = (selector, value) => { const node=$(selector); if(node) node.innerHTML=value == null ? "" : String(value); return node; };
const $$ = selector => [...document.querySelectorAll(selector)];
const state = { status: null, stacks: [], containers: [], currentStack: null, loading: false, auth: { configured: false, authenticated: false, user: null, csrf: null }, hydrated: false, lastRefresh: 0 };
const DASHBOARD_CACHE_KEY = "rogueforge.dashboard.snapshot.v1";
let dashboardRequest=null;
function requestDashboard(force=false){
  if(dashboardRequest)return dashboardRequest;
  dashboardRequest=api("/api/dashboard"+(force?"?refresh=1":"")).finally(()=>{dashboardRequest=null;});
  return dashboardRequest;
}
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
}
state.images=[];state.volumes=[];state.networks=[];state.resourceLoaded={images:false,volumes:false,networks:false};
const pageMeta = {
  overview: ["Command centre", "Overview"],
  stacks: ["Compose workloads", "Stacks"],
  containers: ["Runtime inventory", "Containers"],
  images: ["Runtime resources", "Images"],
  volumes: ["Runtime resources", "Volumes"],
  networks: ["Runtime resources", "Networks"],
  settings: ["RogueForge", "Settings"]
};

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "content-type": "application/json" }, ...options });
  let data;
  try { data = await response.json(); } catch { data = {}; }
  if (response.status === 401 && !path.endsWith("/auth/login")) {
    state.auth = { configured: true, authenticated: false, user: null, csrf: null };
    renderAuth();
  }
  if (!response.ok) throw new Error(data.error || data.output || `Request failed (${response.status})`);
  return data;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function attr(value) { return escapeHtml(value).replace(/`/g, "&#96;"); }

function toast(message, type = "success") {
  const item = document.createElement("div");
  item.className = `toast ${type}`;
  item.textContent = message;
  $("#toasts").append(item);
  setTimeout(() => item.remove(), 4200);
}

function protectedOptions(options = {}) {
  return { ...options, headers: { "content-type": "application/json", "x-csrf-token": state.auth.csrf || "", ...(options.headers || {}) } };
}

function ensureAuthenticated() {
  if (state.auth.authenticated) return true;
  const authInfo = state.auth.auth || {};
  $("#loginError").textContent = state.auth.configured ? "" : (authInfo.exists ? "Administrator credentials could not be read or validated." : "No administrator account has been provisioned yet.");
  $("#loginDialog").showModal();
  setTimeout(() => $("#loginUsername").focus(), 50);
  return false;
}

function renderAuth() {
  const button = $("#accountButton");
  button.classList.toggle("authenticated", state.auth.authenticated);
  button.textContent = state.auth.authenticated ? String(state.auth.user || "A").slice(0, 2).toUpperCase() : "Sign in";
  button.title = state.auth.authenticated ? `Signed in as ${state.auth.user}` : "Sign in for protected operations";
}

function setView(name) {
  $$(".view").forEach(view => view.classList.toggle("active", view.id === `view-${name}`));
  $$(".nav-item[data-view]").forEach(item => item.classList.toggle("active", item.dataset.view === name));
  $("#pageEyebrow").textContent = pageMeta[name][0];
  $("#pageTitle").textContent = pageMeta[name][1];
  $("#sidebar").classList.remove("open");
  history.replaceState(null, "", `#${name}`);
  if(["images","volumes","networks"].includes(name)) loadResource(name);
}


function resourceValue(value){return value==null||value===""?"—":String(value);}
function renderImages(){
  const rows=state.images||[];setText("#imageNavCount",rows.length);setHtml("#imageSummary",`<article><span>Total images</span><strong>${rows.length}</strong><small>Local engine inventory</small></article><article><span>In use</span><strong>${rows.filter(x=>x.inUse).length}</strong><small>Referenced by containers</small></article><article><span>Unused</span><strong>${rows.filter(x=>!x.inUse).length}</strong><small>Potentially reclaimable</small></article>`);
  setHtml("#imageGrid",rows.map(x=>`<article class="resource-card"><div class="resource-icon">⇩</div><div class="resource-main"><strong>${escapeHtml(x.repository)}<span class="resource-tag">:${escapeHtml(x.tag)}</span></strong><small>${escapeHtml(x.shortId||"unknown")}</small><div class="resource-users">${x.inUse?`<span class="resource-use in-use">In use · ${x.containerCount}</span>${(x.containers||[]).slice(0,4).map(c=>`<span>${escapeHtml(c.name)}</span>`).join("")}`:'<span class="resource-use unused">Unused</span>'}</div></div><div class="resource-meta"><span>Size <b>${escapeHtml(resourceValue(x.size))}</b></span><span>Created <b>${escapeHtml(resourceValue(x.created))}</b></span></div></article>`).join("")||'<div class="empty-state">No local images found.</div>');
}
function renderVolumes(){
  const rows=state.volumes||[];setText("#volumeNavCount",rows.length);setHtml("#volumeSummary",`<article><span>Total volumes</span><strong>${rows.length}</strong><small>Persistent storage objects</small></article><article><span>Attached</span><strong>${rows.filter(x=>x.inUse).length}</strong><small>Mounted by containers</small></article><article><span>Unused</span><strong>${rows.filter(x=>!x.inUse).length}</strong><small>No detected container mount</small></article>`);
  setHtml("#volumeGrid",rows.map(x=>`<article class="resource-card"><div class="resource-icon">◉</div><div class="resource-main"><strong>${escapeHtml(x.name)}</strong><small>${escapeHtml(resourceValue(x.mountpoint))}</small><div class="resource-users">${x.inUse?`<span class="resource-use in-use">Attached · ${x.containerCount}</span>${(x.containers||[]).slice(0,4).map(c=>`<span title="${escapeHtml((c.destinations||[]).join(", "))}">${escapeHtml(c.name)}</span>`).join("")}`:'<span class="resource-use unused">Unused</span>'}</div></div><div class="resource-meta"><span>Driver <b>${escapeHtml(resourceValue(x.driver))}</b></span><span>Scope <b>${escapeHtml(resourceValue(x.scope))}</b></span></div></article>`).join("")||'<div class="empty-state">No volumes found.</div>');
}
function renderNetworks(){
  const rows=state.networks||[];setText("#networkNavCount",rows.length);setHtml("#networkSummary",`<article><span>Total networks</span><strong>${rows.length}</strong><small>Engine network inventory</small></article><article><span>Connected</span><strong>${rows.filter(x=>x.inUse).length}</strong><small>Networks with members</small></article><article><span>Unused</span><strong>${rows.filter(x=>!x.inUse).length}</strong><small>No detected members</small></article>`);
  setHtml("#networkGrid",rows.map(x=>`<article class="resource-card"><div class="resource-icon">⌘</div><div class="resource-main"><strong>${escapeHtml(x.name)}</strong><small>${escapeHtml(x.shortId||"engine network")}</small><div class="resource-users">${x.inUse?`<span class="resource-use in-use">Members · ${x.containerCount}</span>${(x.containers||[]).slice(0,5).map(c=>`<span>${escapeHtml(c.name)}</span>`).join("")}`:'<span class="resource-use unused">Unused</span>'}</div></div><div class="resource-meta"><span>Driver <b>${escapeHtml(resourceValue(x.driver))}</b></span><span>Scope <b>${escapeHtml(resourceValue(x.scope))}</b></span></div></article>`).join("")||'<div class="empty-state">No networks found.</div>');
}
async function loadResource(kind,{force=false}={}){
  if(!["images","volumes","networks"].includes(kind))return;
  if(state.resourceLoaded[kind]&&!force)return;
  const grid=$("#"+kind.slice(0,-1)+"Grid");if(grid)grid.innerHTML='<div class="empty-state">Loading engine inventory…</div>';
  try{
    state[kind]=await api("/api/"+kind+(force?"?refresh=1":""));state.resourceLoaded[kind]=true;
    ({images:renderImages,volumes:renderVolumes,networks:renderNetworks})[kind]();
  }catch(error){if(grid)grid.innerHTML=`<div class="empty-state">Unable to load ${escapeHtml(kind)}: ${escapeHtml(error.message)}</div>`;toast(error.message,"error");}
}

function formatPorts(ports) {
  if (!ports?.length) return "—";
  return ports.slice(0, 3).map(port => port.PublicPort ? `${port.PublicPort}:${port.PrivatePort}` : `${port.PrivatePort}/${port.Type || "tcp"}`).join(", ");
}

function stateBadge(value) {
  const normalized = ["running", "partial"].includes(value) ? value : "stopped";
  return `<span class="state-badge ${normalized}">${escapeHtml(normalized)}</span>`;
}

function serviceLogo(key) {
  const initial = String(key || "?").charAt(0).toUpperCase();
  return `<span class="service-logo"><img src="/api/icons/${encodeURIComponent(key)}" alt=""><b>${escapeHtml(initial)}</b></span>`;
}

function stackActions(stack, compact = false) {
  if (stack.managed === false) {
    return `<span class="service-count" title="RogueForge protects its own Compose project from in-app lifecycle operations">Self-managed externally</span>`;
  }
  if (compact) {
    return `<button class="small-button accent" data-edit-stack="${attr(stack.name)}">Compose</button><button class="small-button" data-stack-action="restart" data-stack="${attr(stack.name)}">Restart</button>`;
  }
  return `
    <button class="primary-action" data-stack-action="start" data-stack="${attr(stack.name)}">Start</button>
    <button data-stack-action="stop" data-stack="${attr(stack.name)}">Stop</button>
    <button data-stack-action="restart" data-stack="${attr(stack.name)}">Restart</button>
    <button data-stack-action="pull" data-stack="${attr(stack.name)}">Pull</button>
    <button data-stack-action="recreate" data-stack="${attr(stack.name)}">Recreate</button>
    <button data-edit-stack="${attr(stack.name)}">Edit</button>`;
}

function renderOverview() {
  const running = state.containers.filter(item => item.state === "running").length;
  setText("#stackCount", state.stacks.length);
  setText("#containerCount", state.containers.length);
  setText("#runningCount", running);
  setText("#attentionCount", state.containers.length - running);
  setText("#stackCaption", `${state.stacks.filter(item => item.state === "running").length} fully active`);
  setText("#containerCaption", `Across ${state.status?.engine || "runtime"}`);
  const rows = state.stacks.slice(0, 5).map(stack => `
    <div class="stack-row">
      <div class="stack-identity">${serviceLogo(stack.name)}<div><strong>${escapeHtml(stack.name)}</strong><small>${escapeHtml(stack.composeFile)}</small></div></div>
      ${stateBadge(stack.state)}
      <span class="service-count">${stack.running}/${stack.services} running</span>
      <div class="row-actions">${stackActions(stack, true)}</div>
    </div>`).join("");
  setHtml("#overviewStacks", rows || '<div class="empty-state">No Compose stacks found in the configured directory.</div>');
}

function renderStacks() {
  const query = $("#stackSearch").value.trim().toLowerCase();
  const stacks = state.stacks.filter(stack => stack.name.toLowerCase().includes(query) || stack.composeFile.toLowerCase().includes(query));
  $("#stackGrid").innerHTML = stacks.map(stack => {
    const progress = stack.services ? Math.round(stack.running / stack.services * 100) : 0;
    return `<article class="stack-card">
      <div class="stack-card-top">
        <header><div class="stack-title">${serviceLogo(stack.name)}<div><h3>${escapeHtml(stack.name)}</h3><div class="file">${escapeHtml(stack.composeFile)}</div></div></div>${stateBadge(stack.state)}</header>
        <div class="stack-health"><div class="health-track"><i style="width:${progress}%"></i></div><strong>${progress}%</strong></div>
        <div class="stack-meta"><span>${stack.services} services</span><span>${stack.hasEnv ? ".env linked" : "No .env"}</span><span>${stack.managed === false ? "protected self stack" : escapeHtml(stack.engineHint)}</span></div>
      </div>
      <div class="stack-card-actions">${stackActions(stack)}</div>
    </article>`;
  }).join("") || '<div class="empty-state">No stacks match this filter.</div>';
}

function renderContainers() {
  const query = $("#containerSearch").value.trim().toLowerCase();
  const containers = state.containers.filter(item => [item.name, item.image, item.state].some(value => String(value).toLowerCase().includes(query)));
  $("#containerGrid").innerHTML = `<div class="container-head"><span>Container</span><span>Image</span><span>State</span><span>Ports</span><span></span></div>` + containers.map(container => `
    <div class="container-row">
      <div class="container-name">${serviceLogo(container.name)}<div><strong>${escapeHtml(container.name)}</strong><small>${escapeHtml(container.id)}</small></div></div>
      <span class="image-name" title="${attr(container.image)}">${escapeHtml(container.image)}</span>
      ${stateBadge(container.state)}
      <span class="port-list">${escapeHtml(formatPorts(container.ports))}</span>
      <div class="container-actions"><button class="small-button" data-container-action="restart" data-container="${container.id}">Restart</button><button class="small-button accent" data-logs="${container.id}" data-name="${attr(container.name)}">Logs</button></div>
    </div>`).join("") || '<div class="empty-state">No containers match this filter.</div>';
}

function renderStatus() {
  if (!state.status) return;
  const engine = state.status.engine || "unknown";
  setText("#engineName", `${engine} connected`);
  setText("#engineDetail", state.status.socket || "Protected");
  setText("#engineRuntime", engine);
  setText("#engineInitial", engine.charAt(0).toUpperCase());
  setText("#engineVersion", state.status.version);
  setText("#apiVersion", state.status.apiVersion);
  setText("#socketPath", state.status.socket);
  setText("#engineContext", state.status.context || "default");
  setText("#stacksPath", state.status.stacksDir);
  setText("#publicUrl", state.status.publicUrl || "Not configured");
  setText("#appVersion", state.status.appVersion ? `v${state.status.appVersion}` : "—");
  setText("#stackNavCount", state.stacks.length);
  setText("#containerNavCount", state.containers.length);
}

function renderAll() { renderStatus(); renderOverview(); renderStacks(); renderContainers(); }

async function load({ quiet = false, force = false } = {}) {
  const ownsLoading=!state.loading;
  if(ownsLoading){state.loading=true;$("#refreshButton").classList.add("spinning");}
  try {
    const snapshot = await requestDashboard(force);
    state.status = snapshot.status;
    state.stacks = snapshot.stacks || [];
    state.containers = snapshot.containers || [];
    state.auth = snapshot.auth || state.auth;
    state.hydrated = true;
    state.lastRefresh = Date.now();
    saveDashboardSnapshot(snapshot);
    renderAll();
    renderAuth();
    if (!quiet) toast("Infrastructure refreshed");
  } catch (error) {
    setText("#engineName", "Connection error");
    setText("#engineDetail", error.message);
    toast(error.message, "error");
  } finally {
    if(ownsLoading){state.loading=false;$("#refreshButton").classList.remove("spinning");}
  }
}

async function refreshRuntimeInventory(){
  await load({quiet:true,force:true});
}

function confirmAction(title, message, button = "Continue") {
  $("#confirmTitle").textContent = title;
  $("#confirmMessage").textContent = message;
  $("#confirmButton").textContent = button;
  const dialog = $("#confirmDialog");
  dialog.showModal();
  return new Promise(resolve => dialog.addEventListener("close", () => resolve(dialog.returnValue === "confirm"), { once: true }));
}

async function stackAction(name, action) {
  if (!ensureAuthenticated()) return;
  const prompts = {
    stop: "Stops the services without removing the Compose project.",
    restart: "Restarts the services without taking the Compose project down.",
    recreate: "Recreates the project containers with the current Compose definition."
  };
  if (prompts[action] && !await confirmAction(`${action[0].toUpperCase() + action.slice(1)} ${name}?`, prompts[action], action[0].toUpperCase() + action.slice(1))) return;
  try {
    toast(`${action[0].toUpperCase() + action.slice(1)} started for ${name}`);
    const result = await api(`/api/stacks/${encodeURIComponent(name)}/${action}`, protectedOptions({ method: "POST" }));
    if (result.output) console.info(result.output);
    toast(`${name}: ${action} completed`);
    await refreshRuntimeInventory();
  } catch (error) { toast(error.message, "error"); }
}

async function containerAction(id, action) {
  if (!ensureAuthenticated()) return;
  if (!await confirmAction(`${action[0].toUpperCase() + action.slice(1)} container?`, "The selected container may be briefly unavailable.", action[0].toUpperCase() + action.slice(1))) return;
  try { await api(`/api/containers/${id}/${action}`, protectedOptions({ method: "POST" })); toast(`Container ${action} completed`); setTimeout(() => load({ quiet: true }), 700); }
  catch (error) { toast(error.message, "error"); }
}

async function editStack(name) {
  if (!ensureAuthenticated()) return;
  try {
    const data = await api(`/api/stacks/${encodeURIComponent(name)}/compose`);
    state.currentStack = name;
    $("#editorTitle").textContent = name;
    $("#editorFile").textContent = data.name;
    $("#composeText").value = data.content;
    $("#editorDialog").showModal();
  } catch (error) { toast(error.message, "error"); }
}

async function saveCompose() {
  if (!ensureAuthenticated()) return;
  const button = $("#saveCompose");
  button.disabled = true;
  button.textContent = "Validating…";
  try {
    await api(`/api/stacks/${encodeURIComponent(state.currentStack)}/compose`, protectedOptions({ method: "PUT", body: JSON.stringify({ content: $("#composeText").value }) }));
    $("#editorDialog").close();
    toast("Compose validated, backed up, and saved");
    await load({ quiet: true });
  } catch (error) { toast(error.message, "error"); }
  finally { button.disabled = false; button.textContent = "Validate & save"; }
}

async function showLogs(id, name) {
  if (!ensureAuthenticated()) return;
  $("#logsTitle").textContent = name;
  $("#logText").textContent = "Loading logs…";
  $("#logsDialog").showModal();
  try { $("#logText").textContent = (await api(`/api/containers/${id}/logs`)).logs || "No log output."; }
  catch (error) { $("#logText").textContent = error.message; }
}

async function login(event) {
  event.preventDefault();
  const button = $("#loginButton");
  button.disabled = true;
  $("#loginError").textContent = "";
  try {
    const result = await api("/api/auth/login", { method: "POST", body: JSON.stringify({ username: $("#loginUsername").value, password: $("#loginPassword").value }) });
    state.auth = { configured: true, authenticated: true, user: result.user, csrf: result.csrf };
    $("#loginPassword").value = "";
    $("#loginDialog").close();
    renderAuth();
    await load({ quiet: true });
    toast(`Signed in as ${result.user}`);
  } catch (error) { $("#loginError").textContent = error.message; }
  finally { button.disabled = false; }
}

async function accountAction() {
  if (!state.auth.authenticated) { ensureAuthenticated(); return; }
  if (!await confirmAction("Sign out?", `End the administrator session for ${state.auth.user}?`, "Sign out")) return;
  try {
    await api("/api/auth/logout", protectedOptions({ method: "POST" }));
    state.auth = { configured: true, authenticated: false, user: null, csrf: null };
    renderAuth();
    await load({ quiet: true });
    toast("Signed out");
  } catch (error) { toast(error.message, "error"); }
}

document.addEventListener("click", event => {
  const resourceRefresh=event.target.closest("[data-resource-refresh]");if(resourceRefresh)loadResource(resourceRefresh.dataset.resourceRefresh,{force:true});
  const nav = event.target.closest("[data-view]"); if (nav && !nav.classList.contains("disabled")) setView(nav.dataset.view);
  const go = event.target.closest("[data-go]"); if (go) setView(go.dataset.go);
  const stack = event.target.closest("[data-stack-action]"); if (stack) stackAction(stack.dataset.stack, stack.dataset.stackAction);
  const container = event.target.closest("[data-container-action]"); if (container) containerAction(container.dataset.container, container.dataset.containerAction);
  const editor = event.target.closest("[data-edit-stack]"); if (editor) editStack(editor.dataset.editStack);
  const logs = event.target.closest("[data-logs]"); if (logs) showLogs(logs.dataset.logs, logs.dataset.name);
});
document.addEventListener("error", event => {
  if (event.target.matches?.(".service-logo img")) event.target.closest(".service-logo").classList.add("fallback");
}, true);
$("#menuButton").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
$("#refreshButton").addEventListener("click", () => load({force:true}));
$("#saveCompose").addEventListener("click", saveCompose);
$("#loginForm").addEventListener("submit", login);
$("#accountButton").addEventListener("click", accountAction);
$("#closeLogin").addEventListener("click", () => $("#loginDialog").close());
$("#cancelLogin").addEventListener("click", () => $("#loginDialog").close());
$("#stackSearch").addEventListener("input", renderStacks);
$("#containerSearch").addEventListener("input", renderContainers);
setView(pageMeta[location.hash.slice(1)] ? location.hash.slice(1) : "overview");
hydrateDashboardSnapshot();
load({ quiet: true });
// Runtime inventory refreshes independently of CPU/RAM stats. Slow stats collection in
// container-controls.js must never block the main dashboard from becoming interactive.
setInterval(() => { if(!document.hidden) load({ quiet: true }); }, 10000);
document.addEventListener("visibilitychange", () => {
  if(!document.hidden && Date.now()-state.lastRefresh>5000) load({ quiet: true });
});

/* Canonical stack-first UI and resilience layer. */
const RF_ICON_BASE='https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg';
const RF_ICON_ALIASES={
  'nginx-proxy-manager':'nginx-proxy-manager',
  'npm':'nginx-proxy-manager',
  'qbittorrent':'qbittorrent',
  'q-bittorrent':'qbittorrent',
  'uptime-kuma':'uptime-kuma',
  'cloudflared':'cloudflare',
  'cloudflare-tunnel':'cloudflare',
  'rogue-dashboard':'dashboard-icons',
  'rogue-dashboard-agent':'dashboard-icons',
  'seerr':'seerr',
  'jellyseerr':'jellyseerr',
  'overseerr':'overseerr',
  'flaresolverr':'flaresolverr',
  'tautulli':'tautulli',
  'prowlarr':'prowlarr',
  'radarr':'radarr',
  'sonarr':'sonarr',
  'bazarr':'bazarr',
  'dozzle':'dozzle',
  'plex':'plex'
};
const rfExpandedStacks=new Set();
let rfEnvStack=null;

pageMeta.containers=['Advanced runtime','Runtime'];

function rfIconKey(value){
  let raw=String(value||'generic').toLowerCase().split('@')[0].split(':')[0].split('/').pop();
  raw=raw.replace(/^lscr\.io-/,'').replace(/^linuxserver-/,'').replace(/[_\s]+/g,'-').replace(/[^a-z0-9-]+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'');
  for(const suffix of ['-server','-web','-app','-container']) if(raw.endsWith(suffix)) raw=raw.slice(0,-suffix.length);
  return RF_ICON_ALIASES[raw]||raw||'generic';
}
function rfIconFallback(img,key){
  const step=Number(img.dataset.fallback||0);
  if(step===0){img.dataset.fallback='1';img.src=`${RF_ICON_BASE}/${encodeURIComponent(key)}-dark.svg`;return;}
  if(step===1){img.dataset.fallback='2';img.src=`/api/icons/${encodeURIComponent(key)}`;return;}
  if(step===2){img.dataset.fallback='3';img.src=`${RF_ICON_BASE}/docker.svg`;return;}
  img.style.display='none';
}
serviceLogo=function serviceLogoV080(key){
  const k=rfIconKey(key),initial=String(key||'?').charAt(0).toUpperCase();
  return `<span class="service-logo"><img src="${RF_ICON_BASE}/${encodeURIComponent(k)}.svg" alt="${attr(key||'service')} icon" loading="lazy" data-fallback="0" onerror="rfIconFallback(this,'${attr(k)}')"><b>${escapeHtml(initial)}</b></span>`;
};

function rfStackMembers(stack){return state.containers.filter(c=>c.project===stack.name || c.project===stack.displayName || c.projectDisplay===stack.displayName);}
function rfStatsFor(c){if(typeof rfContainer==='undefined')return{};return rfContainer.stats[c.id?.slice(0,12)]||rfContainer.stats[c.name]||{};}
function rfStackUsage(stack){const members=rfStackMembers(stack);let cpu='—',mem='—';if(members.length){const s=rfStatsFor(members[0]);cpu=s.cpu||'—';mem=s.memory||'—';}return{cpu,mem};}
function rfHealthText(stack){return stack.running===stack.services&&stack.services>0?'All services healthy':stack.running?`${stack.running}/${stack.services} services running`:'Services stopped';}
function rfPath(stack){return stack.relativePath&&stack.relativePath!=='.'?`${state.status?.stacksDir||'/opt/media-server'}/${stack.relativePath}`:(state.status?.stacksDir?`${state.status.stacksDir}/${stack.name}`:stack.name);}

renderOverview=function renderOverviewCanonical(){
  const running=state.containers.filter(c=>c.state==='running').length,stopped=Math.max(0,state.containers.length-running),healthy=state.stacks.filter(s=>s.state==='running').length;
  const root=$('#view-overview');if(!root)return;
  root.innerHTML=`
  <div class="rf-overview-head"><div><h2>Overview</h2><p>System overview and quick actions</p></div><div class="top-actions"><button class="button primary" data-go="stacks">Manage Stacks</button><button class="button secondary" id="rfRefreshOverview">↻ Refresh</button></div></div>
  <section class="rf-summary">
    <article class="rf-summary-card purple"><span class="rf-summary-icon">◇</span><div><span>Total Stacks</span><strong>${state.stacks.length}</strong><small>${healthy} fully running</small></div></article>
    <article class="rf-summary-card cyan"><span class="rf-summary-icon">▣</span><div><span>Total Services</span><strong>${state.containers.length}</strong><small>Across all stacks/runtime</small></div></article>
    <article class="rf-summary-card green"><span class="rf-summary-icon">▷</span><div><span>Running</span><strong>${running}</strong><small>${state.containers.length?Math.round(running/state.containers.length*100):0}% of services</small></div></article>
    <article class="rf-summary-card red"><span class="rf-summary-icon">□</span><div><span>Stopped</span><strong>${stopped}</strong><small>Needs attention</small></div></article>
    <article class="rf-summary-card teal"><span class="rf-summary-icon">♡</span><div><span>Healthy Stacks</span><strong>${healthy}</strong><small>${state.stacks.length?Math.round(healthy/state.stacks.length*100):0}% healthy</small></div></article>
  </section>
  <div class="rf-dashboard"><section class="rf-panel"><div class="rf-panel-head"><h3>Recent Stacks</h3><button class="small-button" data-go="stacks">View all</button></div><div>${state.stacks.slice(0,6).map(stack=>{const u=rfStackUsage(stack);return `<div class="rf-stack-row"><div class="rf-stack-id">${serviceLogo(stack.displayName||stack.name)}<div><strong>${escapeHtml(stack.displayName||stack.name)}</strong>${stateBadge(stack.state)}<small>${escapeHtml(rfPath(stack))}</small></div></div><div class="rf-stack-services"><span class="rf-advanced-label">Services</span><strong>${stack.services}</strong></div><div class="rf-usage">CPU ${escapeHtml(u.cpu)}<br>RAM ${escapeHtml(u.mem)}</div><div class="rf-healthy">✓ ${escapeHtml(rfHealthText(stack))}</div><button class="small-button rf-manage-button" data-go-stack="${attr(stack.name)}">Manage</button></div>`}).join('')||'<div class="empty-state">No Compose stacks discovered.</div>'}</div></section>
  <aside class="rf-side-stack"><section class="rf-panel"><div class="rf-panel-head"><h3>System Information</h3></div><div class="rf-system-list"><div><span>Container Engine</span><b>${escapeHtml(state.status.engine)}</b></div><div><span>Engine Version</span><b>${escapeHtml(state.status.version)}</b></div><div><span>API Version</span><b>${escapeHtml(state.status.apiVersion)}</b></div><div><span>Context</span><b>${escapeHtml(state.status.context||'default')}</b></div><div><span>RogueForge</span><b>v${escapeHtml(state.status.appVersion)}</b></div></div></section><section class="rf-panel"><div class="rf-panel-head"><h3>Quick Actions</h3></div><div class="rf-quick-actions">
    <button class="rf-quick" data-go="stacks"><span class="rf-quick-icon purple">◇</span><b>Stacks</b><small>Manage workloads</small></button>
    <button class="rf-quick" id="rfUpdateAll"><span class="rf-quick-icon blue">⇩</span><b>Update All</b><small>Pull current images</small></button>
    <button class="rf-quick" data-go="containers"><span class="rf-quick-icon violet">⬡</span><b>Runtime</b><small>Advanced container view</small></button>
    <button class="rf-quick" data-go="settings"><span class="rf-quick-icon green">▦</span><b>System Info</b><small>Runtime settings</small></button>
    <button class="rf-quick" id="rfDiscovery"><span class="rf-quick-icon amber">⌕</span><b>Discovery</b><small>Inspect Compose mapping</small></button>
  </div></section></aside></div>`;
}

function rfServiceActions(container){const running=container.state==='running';let out='';if(!container.selfProtected){out+=`<button class="small-button ${running?'':'accent'}" data-container-action="${running?'stop':'start'}" data-container="${container.id}" data-name="${attr(container.name)}">${running?'Stop':'Start'}</button>`;if(running)out+=`<button class="small-button" data-container-action="restart" data-container="${container.id}" data-name="${attr(container.name)}">Restart</button>`;if(container.composeManaged)out+=`<button class="small-button accent" data-container-action="update" data-container="${container.id}" data-name="${attr(container.name)}">Update</button>`;}out+=`<button class="small-button" data-live-logs="${container.id}" data-name="${attr(container.name)}">Logs</button>`;if(running)out+=`<button class="small-button" data-terminal="${container.id}" data-name="${attr(container.name)}">Terminal</button>`;return out;}

renderStacks=function renderStacksCanonical(){
  const grid=$('#stackGrid');if(!grid)return;
  const query=($('#stackSearch')?.value||'').trim().toLowerCase();const stacks=state.stacks.filter(s=>[s.name,s.displayName,s.composeFile,s.relativePath].some(v=>String(v||'').toLowerCase().includes(query)));
  grid.className='rf-stack-list';
  grid.innerHTML=stacks.map(stack=>{const members=rfStackMembers(stack),u=rfStackUsage(stack),expanded=rfExpandedStacks.has(stack.name),managed=stack.managed!==false;return `<article class="rf-stack-card" id="rf-stack-${attr(stack.name)}"><div class="rf-stack-main"><div class="rf-stack-title">${serviceLogo(stack.displayName||stack.name)}<div><h3>${escapeHtml(stack.displayName||stack.name)} ${stateBadge(stack.state)}</h3><small>${escapeHtml(rfPath(stack))}</small><small>${escapeHtml(stack.composeFile)} · ${escapeHtml(stack.discoverySource||'discovered')}</small></div></div><div class="rf-service-dots"><span class="rf-advanced-label">Services (${members.length||stack.services})</span>${members.slice(0,4).map(c=>`<div><b>●</b> ${escapeHtml(c.service||c.name)}</div>`).join('')||'<div>No running service metadata</div>'}</div><div class="rf-stack-stats">CPU ${escapeHtml(u.cpu)}<br>RAM ${escapeHtml(u.mem)}<br><span class="rf-healthy">✓ ${escapeHtml(rfHealthText(stack))}</span></div><div class="rf-stack-actions">${managed?`<button class="small-button" data-stack-action="start" data-stack="${attr(stack.name)}">Start</button><button class="small-button" data-stack-action="stop" data-stack="${attr(stack.name)}">Stop</button><button class="small-button" data-stack-action="restart" data-stack="${attr(stack.name)}">Restart</button><button class="small-button accent" data-rf-stack-update="${attr(stack.name)}">Update</button><button class="small-button" data-rf-config="${attr(stack.name)}">Edit config</button>`:'<span class="service-count">Self-managed externally</span>'}<button class="small-button" data-rf-expand="${attr(stack.name)}">${expanded?'Hide':'Services'} ▾</button></div></div><div class="rf-stack-expand" ${expanded?'':'hidden'}>${members.map(c=>{const st=rfStatsFor(c);return `<div class="rf-service-row"><div class="rf-service-name">${serviceLogo(c.service||c.name)}<div><strong>${escapeHtml(c.service||c.name)}</strong><small>${escapeHtml(c.image)}</small></div></div>${stateBadge(c.state)}<div class="rf-usage">CPU ${escapeHtml(st.cpu||'—')} · RAM ${escapeHtml(st.memory||'—')}</div><div class="rf-service-actions">${rfServiceActions(c)}</div></div>`}).join('')||'<div class="empty-state">No containers currently associated. The Compose definition is still manageable.</div>'}</div></article>`}).join('')||'<div class="empty-state">No stacks match this filter.</div>';
};

const rfOriginalRenderContainers=renderContainers;
renderContainers=function renderRuntimeCanonical(){rfOriginalRenderContainers();const view=$('#view-containers .page-intro p');if(view)view.textContent='Advanced runtime view for standalone containers, inspection, live logs, terminal access and low-level troubleshooting.';};

let rfConfigStack=null;
let rfConfigKind='compose';
let rfConfigFiles={compose:{name:'compose.yaml',content:''},env:{name:'.env',content:''}};

function rfEnsureConfigDialog(){
  if($('#rfConfigDialog'))return;
  document.body.insertAdjacentHTML('beforeend',`<dialog id="rfConfigDialog"><div class="modal wide"><header><div><p class="eyebrow">Stack configuration editor</p><h2 id="rfConfigTitle">Stack config</h2></div><button class="close-button" type="button" id="rfConfigClose">×</button></header><div class="editor-toolbar"><div class="top-actions"><button class="small-button accent" type="button" data-rf-config-tab="compose">Compose</button><button class="small-button" type="button" data-rf-config-tab="env">.env</button></div><span id="rfConfigFile">compose.yaml</span><span id="rfConfigStatus">Validated before save · automatic backup</span></div><textarea id="rfConfigText" spellcheck="false" aria-label="Stack configuration editor"></textarea><footer><button class="button secondary" type="button" id="rfConfigCancel">Cancel</button><button class="button primary" type="button" id="rfConfigSave">Validate & save</button></footer></div></dialog>`);
  $('#rfConfigClose').onclick=$('#rfConfigCancel').onclick=()=>$('#rfConfigDialog').close();
  $('#rfConfigSave').onclick=rfSaveConfig;
  $('#rfConfigDialog').addEventListener('click',e=>{const tab=e.target.closest('[data-rf-config-tab]');if(tab)rfSwitchConfig(tab.dataset.rfConfigTab);});
  $('#rfConfigText').addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();rfSaveConfig();}});
}
function rfPersistEditorBuffer(){
  if(!rfConfigFiles[rfConfigKind])return;
  rfConfigFiles[rfConfigKind].content=$('#rfConfigText')?.value??rfConfigFiles[rfConfigKind].content;
}
function rfSwitchConfig(kind){
  if(!['compose','env'].includes(kind)||kind===rfConfigKind)return;
  rfPersistEditorBuffer();rfConfigKind=kind;
  $('#rfConfigText').value=rfConfigFiles[kind].content||'';
  $('#rfConfigFile').textContent=rfConfigFiles[kind].name|| (kind==='env'?'.env':'compose.yaml');
  $('#rfConfigStatus').textContent='Validated before save · automatic backup';
  document.querySelectorAll('[data-rf-config-tab]').forEach(b=>b.classList.toggle('accent',b.dataset.rfConfigTab===kind));
}
async function rfEditConfig(name){
  if(!ensureAuthenticated())return;rfEnsureConfigDialog();
  try{
    const [compose,env]=await Promise.all([
      api(`/api/stacks/${encodeURIComponent(name)}/compose`),
      api(`/api/stacks/${encodeURIComponent(name)}/env`)
    ]);
    rfConfigStack=name;rfConfigKind='compose';
    rfConfigFiles={compose:{name:compose.name||'compose.yaml',content:compose.content||''},env:{name:env.name||'.env',content:env.content||''}};
    $('#rfConfigTitle').textContent=`${name} · configuration`;
    $('#rfConfigText').value=rfConfigFiles.compose.content;
    $('#rfConfigFile').textContent=rfConfigFiles.compose.name;
    $('#rfConfigStatus').textContent='Validated before save · automatic backup';
    document.querySelectorAll('[data-rf-config-tab]').forEach(b=>b.classList.toggle('accent',b.dataset.rfConfigTab==='compose'));
    $('#rfConfigDialog').showModal();
  }catch(e){toast(e.message,'error');}
}
async function rfSaveConfig(){
  if(!rfConfigStack)return;
  const b=$('#rfConfigSave');rfPersistEditorBuffer();b.disabled=true;b.textContent='Validating…';
  try{
    const endpoint=rfConfigKind==='env'?'env':'compose';
    const result=await api(`/api/stacks/${encodeURIComponent(rfConfigStack)}/${endpoint}`,protectedOptions({method:'PUT',body:JSON.stringify({content:rfConfigFiles[rfConfigKind].content})}));
    const backup=result?.backup? ` · backup: ${result.backup}` : '';
    $('#rfConfigStatus').textContent=`Saved and validated${backup}`;
    toast(`${rfConfigStack}: ${rfConfigKind==='env'?'.env':'Compose'} saved and validated`);
    await load({quiet:true});
  }catch(e){$('#rfConfigStatus').textContent='Validation failed · original file retained/restored';toast(e.message,'error');}
  finally{b.disabled=false;b.textContent='Validate & save';}
}

async function rfUpdateStack(name){if(!ensureAuthenticated())return;if(!await confirmAction(`Update ${name}?`,'Pull latest images and redeploy this stack with its current Compose definition.','Update stack'))return;try{toast(`${name}: update started`);const r=await api(`/api/stacks/${encodeURIComponent(name)}/update`,protectedOptions({method:'POST'}));if(r.output)console.info(r.output);toast(`${name}: update complete`);await refreshRuntimeInventory();}catch(e){toast(e.message,'error');}}
function rfEnsureEnvDialog(){if($('#rfEnvDialog'))return;document.body.insertAdjacentHTML('beforeend',`<dialog id="rfEnvDialog"><div class="modal wide"><header><div><p class="eyebrow">Stack environment</p><h2 id="rfEnvTitle">.env</h2></div><button class="close-button" type="button" id="rfEnvClose">×</button></header><div class="editor-toolbar"><span>.env</span><span>Validated through Compose before save</span></div><textarea id="rfEnvText" spellcheck="false" aria-label="Environment file"></textarea><footer><button class="button secondary" type="button" id="rfEnvCancel">Cancel</button><button class="button primary" type="button" id="rfEnvSave">Validate & save</button></footer></div></dialog>`);$('#rfEnvClose').onclick=$('#rfEnvCancel').onclick=()=>$('#rfEnvDialog').close();$('#rfEnvSave').onclick=rfSaveEnv;}
async function rfEditEnv(name){if(!ensureAuthenticated())return;rfEnsureEnvDialog();try{const d=await api(`/api/stacks/${encodeURIComponent(name)}/env`);rfEnvStack=name;$('#rfEnvTitle').textContent=`${name} · .env`;$('#rfEnvText').value=d.content||'';$('#rfEnvDialog').showModal();}catch(e){toast(e.message,'error');}}
async function rfSaveEnv(){if(!rfEnvStack)return;const b=$('#rfEnvSave');b.disabled=true;b.textContent='Validating…';try{await api(`/api/stacks/${encodeURIComponent(rfEnvStack)}/env`,protectedOptions({method:'PUT',body:JSON.stringify({content:$('#rfEnvText').value})}));$('#rfEnvDialog').close();toast(`${rfEnvStack}: .env saved`);await load({quiet:true});}catch(e){toast(e.message,'error');}finally{b.disabled=false;b.textContent='Validate & save';}}
async function rfShowDiscovery(){if(!ensureAuthenticated())return;try{const d=await api('/api/discovery');$('#logsTitle').textContent='Compose discovery';$('#logText').textContent=JSON.stringify(d,null,2);$('#logsDialog').showModal();}catch(e){toast(e.message,'error');}}

function rfBranding(){const nav=[...document.querySelectorAll('.nav-item[data-view]')].find(x=>x.dataset.view==='containers');if(nav){const label=nav.querySelector('span:nth-child(2)');if(label)label.textContent='Runtime';nav.title='Advanced container/runtime troubleshooting';}if(!document.querySelector('.rf-version-card')){$('#sidebar .sidebar-bottom')?.insertAdjacentHTML('beforebegin',`<div class="rf-version-card"><div class="rf-mini-brand"><span class="rf-mini-mark"></span><div><strong>RogueForge <span id="rfSidebarVersion">—</span></strong><small>Stack-first operations</small></div></div></div>`);} }

const rfOldRenderAll=renderAll;renderAll=function renderAllCanonical(){rfOldRenderAll();rfBranding();renderOverview();renderStacks();renderContainers();const v=$('#rfSidebarVersion');if(v&&state.status?.appVersion)v.textContent=`v${state.status.appVersion}`;};

document.addEventListener('click',e=>{const exp=e.target.closest('[data-rf-expand]');if(exp){const n=exp.dataset.rfExpand;rfExpandedStacks.has(n)?rfExpandedStacks.delete(n):rfExpandedStacks.add(n);renderStacks();}const upd=e.target.closest('[data-rf-stack-update]');if(upd)rfUpdateStack(upd.dataset.rfStackUpdate);const cfg=e.target.closest('[data-rf-config]');if(cfg)rfEditConfig(cfg.dataset.rfConfig);const env=e.target.closest('[data-rf-env]');if(env)rfEditEnv(env.dataset.rfEnv);if(e.target.closest('#rfRefreshOverview'))load({force:true});if(e.target.closest('#rfUpdateAll'))updateAllContainers();if(e.target.closest('#rfDiscovery'))rfShowDiscovery();const go=e.target.closest('[data-go-stack]');if(go){setView('stacks');rfExpandedStacks.add(go.dataset.goStack);renderStacks();setTimeout(()=>document.getElementById(`rf-stack-${CSS.escape(go.dataset.goStack)}`)?.scrollIntoView({behavior:'smooth',block:'center'}),50);}});
rfBranding();

/* Canonical UI compatibility/resilience layer. */
(function () {
  const text = (selector, value) => { const node = document.querySelector(selector); if (node) node.textContent = value == null ? '—' : String(value); };
  renderStatus = function renderStatusSafe() {
    if (!state.status) return;
    const engine = state.status.engine || 'unknown';
    text('#engineName', `${engine} connected`); text('#engineDetail', state.status.socket || 'Protected'); text('#engineRuntime', engine); text('#engineInitial', engine.charAt(0).toUpperCase()); text('#engineVersion', state.status.version); text('#apiVersion', state.status.apiVersion); text('#socketPath', state.status.socket); text('#engineContext', state.status.context || 'default'); text('#stacksPath', state.status.stacksDir); text('#publicUrl', state.status.publicUrl || 'Not configured'); text('#appVersion', state.status.appVersion ? `v${state.status.appVersion}` : '—'); text('#stackNavCount', state.stacks?.length || 0); text('#containerNavCount', state.containers?.length || 0); text('#rfSidebarVersion', state.status.appVersion ? `v${state.status.appVersion}` : '—');
  };
  renderAll = function renderAllCanonicalSafe() {
    try { renderStatus(); } catch (error) { console.error('RogueForge status render failed', error); }
    try { rfBranding(); } catch (error) { console.error('RogueForge branding render failed', error); }
    try { renderOverview(); } catch (error) { console.error('RogueForge overview render failed', error); const root=document.querySelector('#view-overview'); if(root)root.innerHTML=`<div class="empty-state">Overview failed to render: ${escapeHtml(error.message)}</div>`; }
    try { renderStacks(); } catch (error) { console.error('RogueForge stacks render failed', error); const root=document.querySelector('#stackGrid'); if(root)root.innerHTML=`<div class="empty-state">Stacks failed to render: ${escapeHtml(error.message)}</div>`; }
    try { renderContainers(); } catch (error) { console.error('RogueForge runtime render failed', error); const root=document.querySelector('#containerGrid'); if(root)root.innerHTML=`<div class="empty-state">Runtime failed to render: ${escapeHtml(error.message)}</div>`; }
  };
  const previousRenderAuth = renderAuth;
  renderAuth = function renderAuthSafe() { const button=document.querySelector('#accountButton'); if(!button)return; try{previousRenderAuth();}catch(error){console.error('RogueForge auth render failed',error);button.textContent=state.auth?.authenticated?String(state.auth.user||'A').slice(0,2).toUpperCase():'Sign in';} };
  const currentRenderStacks=renderStacks; renderStacks=function renderStacksCanonicalResilient(){const grid=document.querySelector('#stackGrid');if(!grid)return;return currentRenderStacks();};
  const currentRenderContainers=renderContainers; renderContainers=function renderRuntimeCanonicalResilient(){const grid=document.querySelector('#containerGrid');if(!grid)return;return currentRenderContainers();};
  window.addEventListener('error',event=>{if(String(event.message||'').includes('textContent'))console.error('RogueForge prevented a DOM render failure from hiding workload data.',event.error||event.message);});
})();
