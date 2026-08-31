// RogueForge canonical operations and runtime-quality layer.
(()=>{
  const CDN='https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg';
  const RAW='https://raw.githubusercontent.com/homarr-labs/dashboard-icons/main/svg';
  const ICON_ALIASES={
    'nginx-proxy-manager':'nginx-proxy-manager','nginxproxymanager':'nginx-proxy-manager','npm':'nginx-proxy-manager','jc21':'nginx-proxy-manager',
    'cloudflared':'cloudflare','cloudflare-tunnel':'cloudflare','cloudflare-zero-trust':'cloudflare','cloudflare':'cloudflare',
    'qbittorrent':'qbittorrent','q-bittorrent':'qbittorrent','uptime-kuma':'uptime-kuma','seerr':'seerr','jellyseerr':'jellyseerr','overseerr':'overseerr',
    'flaresolverr':'flaresolverr','tautulli':'tautulli','prowlarr':'prowlarr','radarr':'radarr','sonarr':'sonarr','bazarr':'bazarr','dozzle':'dozzle','plex':'plex',
    'rogue-dashboard':'dashboard-icons','rogue-dashboard-agent':'dashboard-icons','rogueforge':'dashboard-icons'
  };
  function cleanIconKey(value){
    let raw=String(value||'generic').toLowerCase().trim();
    if(raw.includes('nginx-proxy-manager')||raw.includes('jc21/nginx-proxy-manager'))return'nginx-proxy-manager';
    if(raw.includes('cloudflared')||raw.includes('cloudflare/cloudflared'))return'cloudflare';
    raw=raw.split('@')[0].split(':')[0].split('/').pop().replace(/^lscr\.io-/,'').replace(/^linuxserver-/,'').replace(/[_\s]+/g,'-').replace(/[^a-z0-9-]+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'');
    for(const suffix of ['-server','-web','-app','-container'])if(raw.endsWith(suffix))raw=raw.slice(0,-suffix.length);
    return ICON_ALIASES[raw]||raw||'docker';
  }
  function bestIdentity(key){
    const raw=String(key||'');
    const items=window.state?.containers||[];
    const exact=items.find(c=>c.name===raw||c.service===raw);
    if(exact)return exact.image||exact.service||exact.name||raw;
    const project=items.find(c=>c.project===raw||c.projectDisplay===raw);
    return project?(project.image||project.service||project.name||raw):raw;
  }
  function iconSources(value){const key=cleanIconKey(value),local=encodeURIComponent(String(value||key));return[`${CDN}/${encodeURIComponent(key)}.svg`,`${RAW}/${encodeURIComponent(key)}.svg`,`/api/icons/${local}`,`${CDN}/docker.svg`];}
  function wireIcon(img){
    if(img.dataset.rfIconReady==='1')return;img.dataset.rfIconReady='1';
    const sources=iconSources(img.dataset.rfIcon||img.getAttribute('alt')||'docker');let at=0;img.src=sources[0];
    img.addEventListener('load',()=>{img.style.display='block';img.classList.add('rf-icon-loaded');});
    img.addEventListener('error',()=>{at++;if(at<sources.length){img.src=sources[at];return;}img.style.display='none';});
  }
  window.serviceLogo=serviceLogo=function(key){const identity=bestIdentity(key),initial=String(key||'?').charAt(0).toUpperCase();return`<span class="service-logo rf-service-logo"><img data-rf-icon="${attr(identity||key||'service')}" alt="${attr(key||'service')}" loading="lazy"><b>${escapeHtml(initial)}</b></span>`;};
  function scanIcons(root=document){root.querySelectorAll?.('img[data-rf-icon]').forEach(wireIcon);}
  const observer=new MutationObserver(rs=>rs.forEach(r=>r.addedNodes.forEach(n=>{if(n.nodeType===1){if(n.matches?.('img[data-rf-icon]'))wireIcon(n);scanIcons(n);}})));

  let operations=[];const fmt=t=>new Date(Number(t)*1000).toLocaleString(),duration=o=>o.ended?`${Math.max(0,Number(o.ended)-Number(o.started)).toFixed(1)}s`:'running';
  const nativeFetch=window.fetch.bind(window);
  async function syncOperations(){try{const r=await nativeFetch('/api/operations',{credentials:'same-origin'});if(r.ok){operations=await r.json();renderOperations();}}catch{}}
  async function waitOperation(id){
    for(;;){await new Promise(r=>setTimeout(r,500));const res=await nativeFetch(`/api/operations/${encodeURIComponent(id)}`,{credentials:'same-origin'});if(!res.ok)throw new Error(`Operation status HTTP ${res.status}`);const op=await res.json();const at=operations.findIndex(x=>x.id===op.id);if(at>=0)operations[at]=op;else operations.unshift(op);renderOperations();if(op.status!=='running')return op;}
  }
  function mutationLabel(url,method){const p=new URL(url,location.href).pathname,m=p.match(/^\/api\/stacks\/([^/]+)\/(start|stop|restart|pull|recreate|update)$/);if(!m||method!=='POST')return null;return{scope:'stack',target:decodeURIComponent(m[1]),action:m[2]};}
  window.fetch=async function(input,init={}){
    const url=typeof input==='string'?input:input.url,method=String(init.method||(typeof input!=='string'&&input.method)||'GET').toUpperCase(),meta=mutationLabel(url,method);
    if(!meta)return nativeFetch(input,init);
    const headers=new Headers(init.headers||{});headers.set('content-type','application/json');
    const created=await nativeFetch('/api/operations',{method:'POST',headers,credentials:init.credentials||'same-origin',body:JSON.stringify(meta)});
    if(!created.ok)return created;
    const op=await created.json();operations.unshift(op);renderOperations();const done=await waitOperation(op.id);await syncOperations();
    const ok=done.status==='success',payload={ok,status:done.status,output:done.output||'',operationId:done.id,error:ok?undefined:(done.output||done.status)};
    return new Response(JSON.stringify(payload),{status:ok?200:409,headers:{'content-type':'application/json'}});
  };

  function ensureDrawer(){
    if(document.getElementById('rfOperationsDrawer'))return;
    const button=document.createElement('button');button.type='button';button.id='rfOperationsButton';button.className='icon-button rf-operations-button';button.title='Operations history';button.innerHTML='⌁<span id="rfOperationsCount"></span>';document.querySelector('.top-actions')?.prepend(button);
    document.body.insertAdjacentHTML('beforeend',`<aside id="rfOperationsDrawer" class="rf-operations-drawer" aria-label="Operations"><header><div><p class="eyebrow">Operations</p><h2>Activity</h2></div><button class="close-button" id="rfOperationsClose" type="button">×</button></header><div class="rf-operations-toolbar"><select id="rfOperationsFilter"><option value="all">All operations</option><option value="running">Running</option><option value="success">Successful</option><option value="failed">Failed</option><option value="timed_out">Timed out</option><option value="cancelled">Cancelled</option></select><div><button class="small-button" id="rfOperationsExport" type="button">Export</button></div></div><div id="rfOperationsList" class="rf-operations-list"></div></aside><div id="rfOperationsShade" class="rf-operations-shade"></div>`);
    button.onclick=()=>toggleDrawer(true);document.getElementById('rfOperationsClose').onclick=()=>toggleDrawer(false);document.getElementById('rfOperationsShade').onclick=()=>toggleDrawer(false);document.getElementById('rfOperationsFilter').onchange=renderOperations;
    document.getElementById('rfOperationsExport').onclick=()=>{const blob=new Blob([JSON.stringify(operations,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`rogueforge-operations-${new Date().toISOString().slice(0,10)}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),500);};
    document.getElementById('rfOperationsList').addEventListener('click',async e=>{const b=e.target.closest('[data-rf-cancel-op]');if(!b)return;b.disabled=true;try{await nativeFetch(`/api/operations/${encodeURIComponent(b.dataset.rfCancelOp)}`,{method:'DELETE',...(typeof protectedOptions==='function'?protectedOptions({method:'DELETE'}):{method:'DELETE'}),credentials:'same-origin'});await syncOperations();}finally{b.disabled=false;}});
  }
  function toggleDrawer(open){document.getElementById('rfOperationsDrawer')?.classList.toggle('open',open);document.getElementById('rfOperationsShade')?.classList.toggle('open',open);}
  function renderOperations(){ensureDrawer();const list=document.getElementById('rfOperationsList');if(!list)return;const running=operations.filter(o=>o.status==='running').length,count=document.getElementById('rfOperationsCount');if(count){count.textContent=running||'';count.hidden=!running;}const filter=document.getElementById('rfOperationsFilter')?.value||'all',shown=filter==='all'?operations:operations.filter(o=>o.status===filter);list.innerHTML=shown.map(o=>{const progress=o.stepCount?(`Step ${Number(o.stepIndex||0)}/${Number(o.stepCount)}`):'',timeout=o.timeoutSeconds?(`${Number(o.timeoutSeconds)}s timeout`):'',step=o.currentStep?(` · ${escapeHtml(o.currentStep)}`):'',reason=o.failureReason?`<div class="rf-operation-error">${escapeHtml(o.failureReason)}</div>`:'';return `<article class="rf-operation ${attr(o.status)}"><div class="rf-operation-top"><span class="rf-operation-state">${o.status==='running'?'●':o.status==='success'?'✓':o.status==='timed_out'?'⏱':'!'}</span><div><strong>Stack · ${escapeHtml(o.action)}</strong><small>${escapeHtml(o.target)}</small></div><span class="rf-operation-duration">${escapeHtml(duration(o))}</span></div><div class="rf-operation-meta"><span>${escapeHtml(fmt(o.started))}</span><span>${escapeHtml(String(o.status).replace('_',' '))}</span></div>${(progress||timeout)?`<div class="rf-operation-meta"><span>${escapeHtml(progress)}${step}</span><span>${escapeHtml(timeout)}</span></div>`:''}${reason}${o.status==='running'?`<button class="small-button" data-rf-cancel-op="${attr(o.id)}">Cancel</button>`:''}${o.output?`<details open="${o.status==='running'?'open':''}"><summary>Live output</summary><pre>${escapeHtml(o.output)}</pre></details>`:''}</article>`;}).join('')||'<div class="empty-state">No operations match this filter.</div>';}
  setInterval(()=>{if(operations.some(o=>o.status==='running'))syncOperations();},1000);

  let healthFilter='all';
  function stackHealth(s){if(s.services>0&&s.running===s.services)return'healthy';if(s.running>0)return'partial';return'stopped';}
  function enhanceStackHealth(){
    const grid=document.getElementById('stackGrid');if(!grid||!window.state?.stacks)return;
    let toolbar=document.getElementById('rfHealthFilters');if(!toolbar){toolbar=document.createElement('div');toolbar.id='rfHealthFilters';toolbar.className='rf-health-filters';grid.parentElement?.insertBefore(toolbar,grid);toolbar.addEventListener('click',e=>{const b=e.target.closest('[data-health-filter]');if(!b)return;healthFilter=b.dataset.healthFilter;enhanceStackHealth();});}
    const counts={all:state.stacks.length,healthy:0,partial:0,stopped:0};state.stacks.forEach(s=>counts[stackHealth(s)]++);toolbar.innerHTML=['all','healthy','partial','stopped'].map(k=>`<button class="small-button ${healthFilter===k?'accent':''}" data-health-filter="${k}">${k[0].toUpperCase()+k.slice(1)} <b>${counts[k]}</b></button>`).join('');
    [...grid.querySelectorAll('.rf-stack-card')].forEach(card=>{const id=card.id.replace(/^rf-stack-/,'');const s=state.stacks.find(x=>String(x.name)===id);if(!s)return;const health=stackHealth(s);card.dataset.health=health;card.hidden=healthFilter!=='all'&&health!==healthFilter;card.querySelectorAll('.rf-service-row').forEach(row=>{const badge=row.querySelector('.state-badge');if(badge){row.classList.toggle('rf-service-problem',!badge.classList.contains('running'));}});});
  }
  const oldRenderStacks=window.renderStacks;
  if(typeof oldRenderStacks==='function')window.renderStacks=renderStacks=function(){const r=oldRenderStacks.apply(this,arguments);queueMicrotask(enhanceStackHealth);return r;};
  function boot(){scanIcons();observer.observe(document.body,{childList:true,subtree:true});ensureDrawer();syncOperations();enhanceStackHealth();}
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',boot,{once:true}):boot();
})();
