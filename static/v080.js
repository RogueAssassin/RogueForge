// RogueForge v0.8.0 stack-first UI.
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

renderOverview=function renderOverviewV080(){
  const running=state.containers.filter(c=>c.state==='running').length,stopped=Math.max(0,state.containers.length-running),healthy=state.stacks.filter(s=>s.state==='running').length;
  const root=$('#view-overview');if(!root)return;
  root.innerHTML=`<section class="rf-hero"><img src="https://raw.githubusercontent.com/RogueAssassin/RogueForge/main/docs/assets/rogueforge-banner.png" alt="RogueForge" loading="eager"><div class="rf-hero-shade"></div><div class="rf-hero-copy"><span>ROGUEFORGE v${escapeHtml(state.status?.appVersion||'0.8.0')}</span><h2>Infrastructure under control.</h2><p>Compose-first management for Podman and Docker.</p></div></section>
  <div class="rf-overview-head"><div><h2>Overview</h2><p>System overview and quick actions</p></div><div class="top-actions"><button class="button primary" data-go="stacks">Manage Stacks</button><button class="button secondary" id="rfRefreshOverview">↻ Refresh</button></div></div>
  <section class="rf-summary"><article class="rf-summary-card purple"><span>Total Stacks</span><strong>${state.stacks.length}</strong><small>${healthy} fully running</small></article><article class="rf-summary-card cyan"><span>Total Services</span><strong>${state.containers.length}</strong><small>Across all stacks/runtime</small></article><article class="rf-summary-card green"><span>Running</span><strong>${running}</strong><small>${state.containers.length?Math.round(running/state.containers.length*100):0}% of services</small></article><article class="rf-summary-card red"><span>Stopped</span><strong>${stopped}</strong><small>Needs attention</small></article><article class="rf-summary-card teal"><span>Healthy Stacks</span><strong>${healthy}</strong><small>${state.stacks.length?Math.round(healthy/state.stacks.length*100):0}% healthy</small></article></section>
  <div class="rf-dashboard"><section class="rf-panel"><div class="rf-panel-head"><h3>Recent Stacks</h3><button class="small-button" data-go="stacks">View all</button></div><div>${state.stacks.slice(0,6).map(stack=>{const u=rfStackUsage(stack);return `<div class="rf-stack-row"><div class="rf-stack-id">${serviceLogo(stack.displayName||stack.name)}<div><strong>${escapeHtml(stack.displayName||stack.name)}</strong>${stateBadge(stack.state)}<small>${escapeHtml(rfPath(stack))}</small></div></div><div><span class="rf-advanced-label">Services</span><strong>${stack.services}</strong></div><div class="rf-usage">CPU ${escapeHtml(u.cpu)}<br>RAM ${escapeHtml(u.mem)}</div><div class="rf-healthy">✓ ${escapeHtml(rfHealthText(stack))}</div><button class="small-button" data-go-stack="${attr(stack.name)}">Manage</button></div>`}).join('')||'<div class="empty-state">No Compose stacks discovered.</div>'}</div></section>
  <aside class="rf-side-stack"><section class="rf-panel"><div class="rf-panel-head"><h3>System Information</h3></div><div class="rf-system-list"><div><span>Container Engine</span><b>${escapeHtml(state.status.engine)}</b></div><div><span>Engine Version</span><b>${escapeHtml(state.status.version)}</b></div><div><span>API Version</span><b>${escapeHtml(state.status.apiVersion)}</b></div><div><span>Context</span><b>${escapeHtml(state.status.context||'default')}</b></div><div><span>RogueForge</span><b>v${escapeHtml(state.status.appVersion)}</b></div></div></section><section class="rf-panel"><div class="rf-panel-head"><h3>Quick Actions</h3></div><div class="rf-quick-actions"><button class="rf-quick" data-go="stacks"><b>Stacks</b><small>Manage workloads</small></button><button class="rf-quick" id="rfUpdateAll"><b>Update All</b><small>Pull current images</small></button><button class="rf-quick" data-go="containers"><b>Runtime</b><small>Advanced container view</small></button><button class="rf-quick" data-go="settings"><b>System Info</b><small>Runtime settings</small></button><button class="rf-quick" id="rfDiscovery"><b>Discovery</b><small>Inspect Compose mapping</small></button></div></section></aside></div>`;
};

function rfServiceActions(container){const running=container.state==='running';let out='';if(!container.selfProtected){out+=`<button class="small-button ${running?'':'accent'}" data-container-action="${running?'stop':'start'}" data-container="${container.id}" data-name="${attr(container.name)}">${running?'Stop':'Start'}</button>`;if(running)out+=`<button class="small-button" data-container-action="restart" data-container="${container.id}" data-name="${attr(container.name)}">Restart</button>`;if(container.composeManaged)out+=`<button class="small-button accent" data-container-action="update" data-container="${container.id}" data-name="${attr(container.name)}">Update</button>`;}out+=`<button class="small-button" data-live-logs="${container.id}" data-name="${attr(container.name)}">Logs</button>`;if(running)out+=`<button class="small-button" data-terminal="${container.id}" data-name="${attr(container.name)}">Terminal</button>`;return out;}

renderStacks=function renderStacksV080(){
  const grid=$('#stackGrid');if(!grid)return;
  const query=($('#stackSearch')?.value||'').trim().toLowerCase();const stacks=state.stacks.filter(s=>[s.name,s.displayName,s.composeFile,s.relativePath].some(v=>String(v||'').toLowerCase().includes(query)));
  grid.className='rf-stack-list';
  grid.innerHTML=stacks.map(stack=>{const members=rfStackMembers(stack),u=rfStackUsage(stack),expanded=rfExpandedStacks.has(stack.name),managed=stack.managed!==false;return `<article class="rf-stack-card" id="rf-stack-${attr(stack.name)}"><div class="rf-stack-main"><div class="rf-stack-title">${serviceLogo(stack.displayName||stack.name)}<div><h3>${escapeHtml(stack.displayName||stack.name)} ${stateBadge(stack.state)}</h3><small>${escapeHtml(rfPath(stack))}</small><small>${escapeHtml(stack.composeFile)} · ${escapeHtml(stack.discoverySource||'discovered')}</small></div></div><div class="rf-service-dots"><span class="rf-advanced-label">Services (${members.length||stack.services})</span>${members.slice(0,4).map(c=>`<div><b>●</b> ${escapeHtml(c.service||c.name)}</div>`).join('')||'<div>No running service metadata</div>'}</div><div class="rf-stack-stats">CPU ${escapeHtml(u.cpu)}<br>RAM ${escapeHtml(u.mem)}<br><span class="rf-healthy">✓ ${escapeHtml(rfHealthText(stack))}</span></div><div class="rf-stack-actions">${managed?`<button class="small-button" data-stack-action="start" data-stack="${attr(stack.name)}">Start</button><button class="small-button" data-stack-action="stop" data-stack="${attr(stack.name)}">Stop</button><button class="small-button" data-stack-action="restart" data-stack="${attr(stack.name)}">Restart</button><button class="small-button accent" data-rf-stack-update="${attr(stack.name)}">Update</button><button class="small-button" data-edit-stack="${attr(stack.name)}">Compose</button><button class="small-button" data-rf-env="${attr(stack.name)}">.env</button>`:'<span class="service-count">Self-managed externally</span>'}<button class="small-button" data-rf-expand="${attr(stack.name)}">${expanded?'Hide':'Services'} ▾</button></div></div><div class="rf-stack-expand" ${expanded?'':'hidden'}>${members.map(c=>{const st=rfStatsFor(c);return `<div class="rf-service-row"><div class="rf-service-name">${serviceLogo(c.service||c.name)}<div><strong>${escapeHtml(c.service||c.name)}</strong><small>${escapeHtml(c.image)}</small></div></div>${stateBadge(c.state)}<div class="rf-usage">CPU ${escapeHtml(st.cpu||'—')} · RAM ${escapeHtml(st.memory||'—')}</div><div class="rf-service-actions">${rfServiceActions(c)}</div></div>`}).join('')||'<div class="empty-state">No containers currently associated. The Compose definition is still manageable.</div>'}</div></article>`}).join('')||'<div class="empty-state">No stacks match this filter.</div>';
};

const rfOriginalRenderContainers=renderContainers;
renderContainers=function renderRuntimeV080(){rfOriginalRenderContainers();const view=$('#view-containers .page-intro p');if(view)view.textContent='Advanced runtime view for standalone containers, inspection, live logs, terminal access and low-level troubleshooting.';};

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

async function rfUpdateStack(name){if(!ensureAuthenticated())return;if(!await confirmAction(`Update ${name}?`,'Pull latest images and redeploy this stack with its current Compose definition.','Update stack'))return;try{toast(`${name}: update started`);const r=await api(`/api/stacks/${encodeURIComponent(name)}/update`,protectedOptions({method:'POST'}));if(r.output)console.info(r.output);toast(`${name}: update complete`);await load({quiet:true});}catch(e){toast(e.message,'error');}}
function rfEnsureEnvDialog(){if($('#rfEnvDialog'))return;document.body.insertAdjacentHTML('beforeend',`<dialog id="rfEnvDialog"><div class="modal wide"><header><div><p class="eyebrow">Stack environment</p><h2 id="rfEnvTitle">.env</h2></div><button class="close-button" type="button" id="rfEnvClose">×</button></header><div class="editor-toolbar"><span>.env</span><span>Validated through Compose before save</span></div><textarea id="rfEnvText" spellcheck="false" aria-label="Environment file"></textarea><footer><button class="button secondary" type="button" id="rfEnvCancel">Cancel</button><button class="button primary" type="button" id="rfEnvSave">Validate & save</button></footer></div></dialog>`);$('#rfEnvClose').onclick=$('#rfEnvCancel').onclick=()=>$('#rfEnvDialog').close();$('#rfEnvSave').onclick=rfSaveEnv;}
async function rfEditEnv(name){if(!ensureAuthenticated())return;rfEnsureEnvDialog();try{const d=await api(`/api/stacks/${encodeURIComponent(name)}/env`);rfEnvStack=name;$('#rfEnvTitle').textContent=`${name} · .env`;$('#rfEnvText').value=d.content||'';$('#rfEnvDialog').showModal();}catch(e){toast(e.message,'error');}}
async function rfSaveEnv(){if(!rfEnvStack)return;const b=$('#rfEnvSave');b.disabled=true;b.textContent='Validating…';try{await api(`/api/stacks/${encodeURIComponent(rfEnvStack)}/env`,protectedOptions({method:'PUT',body:JSON.stringify({content:$('#rfEnvText').value})}));$('#rfEnvDialog').close();toast(`${rfEnvStack}: .env saved`);await load({quiet:true});}catch(e){toast(e.message,'error');}finally{b.disabled=false;b.textContent='Validate & save';}}
async function rfShowDiscovery(){if(!ensureAuthenticated())return;try{const d=await api('/api/discovery');$('#logsTitle').textContent='Compose discovery';$('#logText').textContent=JSON.stringify(d,null,2);$('#logsDialog').showModal();}catch(e){toast(e.message,'error');}}

function rfBranding(){const nav=[...document.querySelectorAll('.nav-item[data-view]')].find(x=>x.dataset.view==='containers');if(nav){const label=nav.querySelector('span:nth-child(2)');if(label)label.textContent='Runtime';nav.title='Advanced container/runtime troubleshooting';}if(!document.querySelector('.rf-version-card')){$('#sidebar .sidebar-bottom')?.insertAdjacentHTML('beforebegin',`<div class="rf-version-card"><div class="rf-mini-brand"><span class="rf-mini-mark"></span><div><strong>RogueForge <span id="rfSidebarVersion">v0.8.0</span></strong><small>Stack-first operations</small></div></div></div>`);} }

const rfOldRenderAll=renderAll;renderAll=function renderAllV080(){rfOldRenderAll();rfBranding();renderOverview();renderStacks();renderContainers();const v=$('#rfSidebarVersion');if(v&&state.status?.appVersion)v.textContent=`v${state.status.appVersion}`;};

document.addEventListener('click',e=>{const exp=e.target.closest('[data-rf-expand]');if(exp){const n=exp.dataset.rfExpand;rfExpandedStacks.has(n)?rfExpandedStacks.delete(n):rfExpandedStacks.add(n);renderStacks();}const upd=e.target.closest('[data-rf-stack-update]');if(upd)rfUpdateStack(upd.dataset.rfStackUpdate);const cfg=e.target.closest('[data-rf-config]');if(cfg)rfEditConfig(cfg.dataset.rfConfig);const env=e.target.closest('[data-rf-env]');if(env)rfEditEnv(env.dataset.rfEnv);if(e.target.closest('#rfRefreshOverview'))load();if(e.target.closest('#rfUpdateAll'))updateAllContainers();if(e.target.closest('#rfDiscovery'))rfShowDiscovery();const go=e.target.closest('[data-go-stack]');if(go){setView('stacks');rfExpandedStacks.add(go.dataset.goStack);renderStacks();setTimeout(()=>document.getElementById(`rf-stack-${CSS.escape(go.dataset.goStack)}`)?.scrollIntoView({behavior:'smooth',block:'center'}),50);}});
rfBranding();
