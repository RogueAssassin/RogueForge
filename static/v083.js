// RogueForge v0.8.3 operations-quality and resilient icon resolver.
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
    if(raw.includes('nginx-proxy-manager')||raw.includes('jc21/nginx-proxy-manager')) return 'nginx-proxy-manager';
    if(raw.includes('cloudflared')||raw.includes('cloudflare/cloudflared')) return 'cloudflare';
    raw=raw.split('@')[0].split(':')[0].split('/').pop();
    raw=raw.replace(/^lscr\.io-/,'').replace(/^linuxserver-/,'').replace(/[_\s]+/g,'-').replace(/[^a-z0-9-]+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'');
    for(const suffix of ['-server','-web','-app','-container']) if(raw.endsWith(suffix)) raw=raw.slice(0,-suffix.length);
    return ICON_ALIASES[raw]||raw||'docker';
  }

  function iconSources(value){
    const key=cleanIconKey(value);
    const local=encodeURIComponent(String(value||key));
    return [`${CDN}/${encodeURIComponent(key)}.svg`,`${RAW}/${encodeURIComponent(key)}.svg`,`/api/icons/${local}`,`${CDN}/docker.svg`];
  }

  function wireIcon(img){
    if(img.dataset.rfIconReady==='1')return;
    img.dataset.rfIconReady='1';
    const original=img.dataset.rfIcon||img.getAttribute('alt')||'docker';
    const sources=iconSources(original);let at=0;
    img.src=sources[0];
    img.addEventListener('load',()=>{img.style.display='block';img.classList.add('rf-icon-loaded');});
    img.addEventListener('error',()=>{
      at++;
      if(at<sources.length){img.src=sources[at];return;}
      img.style.display='none';
    });
  }

  // Override the older serviceLogo renderer. The visible initial remains beneath the
  // image, so a service never becomes a blank icon even if every remote source fails.
  window.serviceLogo=serviceLogo=function serviceLogoV083(key){
    const initial=String(key||'?').charAt(0).toUpperCase();
    return `<span class="service-logo rf-service-logo"><img data-rf-icon="${attr(key||'service')}" alt="${attr(key||'service')}" loading="lazy"><b>${escapeHtml(initial)}</b></span>`;
  };

  function scanIcons(root=document){root.querySelectorAll('img[data-rf-icon]').forEach(wireIcon);}
  const iconObserver=new MutationObserver(records=>records.forEach(r=>r.addedNodes.forEach(n=>{if(n.nodeType===1){if(n.matches?.('img[data-rf-icon]'))wireIcon(n);scanIcons(n);}})));
  document.addEventListener('DOMContentLoaded',()=>{scanIcons();iconObserver.observe(document.body,{childList:true,subtree:true});});
  if(document.body){scanIcons();iconObserver.observe(document.body,{childList:true,subtree:true});}

  // ---- Operations quality milestone: activity drawer + persistent history ----
  const HISTORY_KEY='rogueforge-operation-history-v1';
  const MAX_HISTORY=80;
  let operations=[];
  try{operations=JSON.parse(localStorage.getItem(HISTORY_KEY)||'[]');if(!Array.isArray(operations))operations=[];}catch{operations=[];}
  const save=()=>localStorage.setItem(HISTORY_KEY,JSON.stringify(operations.slice(0,MAX_HISTORY)));
  const uid=()=>`${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
  const fmt=t=>new Date(t).toLocaleString();
  const duration=o=>o.ended?`${Math.max(0,(o.ended-o.started)/1000).toFixed(1)}s`:'running';

  function mutationLabel(url,method){
    const p=new URL(url,location.href).pathname;
    const m=p.match(/^\/api\/(stacks|containers)\/([^/]+)\/(.+)$/);
    if(!m)return null;
    const target=decodeURIComponent(m[2]);const action=decodeURIComponent(m[3]).replace(/\//g,' · ');
    if(method==='GET')return null;
    return {scope:m[1]==='stacks'?'Stack':'Container',target,action};
  }
  function addOperation(meta){
    const item={id:uid(),...meta,status:'running',started:Date.now(),ended:null,output:''};operations.unshift(item);operations=operations.slice(0,MAX_HISTORY);save();renderOperations();return item;
  }
  function finishOperation(item,status,output=''){item.status=status;item.ended=Date.now();item.output=String(output||'').slice(-12000);save();renderOperations();}

  const nativeFetch=window.fetch.bind(window);
  window.fetch=async function rfTrackedFetch(input,init={}){
    const url=typeof input==='string'?input:input.url;
    const method=String(init.method||(typeof input!=='string'&&input.method)||'GET').toUpperCase();
    const meta=mutationLabel(url,method);const op=meta?addOperation({...meta,method}):null;
    try{
      const response=await nativeFetch(input,init);
      if(op){
        let output='';try{const clone=response.clone();const type=clone.headers.get('content-type')||'';if(type.includes('json')){const data=await clone.json();output=data.output||data.error||JSON.stringify(data,null,2);}else output=await clone.text();}catch{}
        finishOperation(op,response.ok?'success':'failed',output||`HTTP ${response.status}`);
      }
      return response;
    }catch(error){if(op)finishOperation(op,'failed',error.message);throw error;}
  };

  function ensureDrawer(){
    if(document.getElementById('rfOperationsDrawer'))return;
    const button=document.createElement('button');button.type='button';button.id='rfOperationsButton';button.className='icon-button rf-operations-button';button.title='Operations history';button.innerHTML='⌁<span id="rfOperationsCount"></span>';
    document.querySelector('.top-actions')?.prepend(button);
    document.body.insertAdjacentHTML('beforeend',`<aside id="rfOperationsDrawer" class="rf-operations-drawer" aria-label="Operations"><header><div><p class="eyebrow">Operations</p><h2>Activity</h2></div><button class="close-button" id="rfOperationsClose" type="button">×</button></header><div class="rf-operations-toolbar"><span>Latest stack and container mutations</span><button class="small-button" id="rfOperationsClear" type="button">Clear completed</button></div><div id="rfOperationsList" class="rf-operations-list"></div></aside><div id="rfOperationsShade" class="rf-operations-shade"></div>`);
    button.onclick=()=>toggleDrawer(true);document.getElementById('rfOperationsClose').onclick=()=>toggleDrawer(false);document.getElementById('rfOperationsShade').onclick=()=>toggleDrawer(false);
    document.getElementById('rfOperationsClear').onclick=()=>{operations=operations.filter(o=>o.status==='running');save();renderOperations();};
  }
  function toggleDrawer(open){document.getElementById('rfOperationsDrawer')?.classList.toggle('open',open);document.getElementById('rfOperationsShade')?.classList.toggle('open',open);}
  function renderOperations(){
    ensureDrawer();const list=document.getElementById('rfOperationsList');if(!list)return;
    const running=operations.filter(o=>o.status==='running').length;const count=document.getElementById('rfOperationsCount');if(count){count.textContent=running||'';count.hidden=!running;}
    list.innerHTML=operations.map(o=>`<article class="rf-operation ${attr(o.status)}"><div class="rf-operation-top"><span class="rf-operation-state">${o.status==='running'?'●':o.status==='success'?'✓':'!'}</span><div><strong>${escapeHtml(o.scope)} · ${escapeHtml(o.action)}</strong><small>${escapeHtml(o.target)}</small></div><span class="rf-operation-duration">${escapeHtml(duration(o))}</span></div><div class="rf-operation-meta"><span>${escapeHtml(fmt(o.started))}</span><span>${escapeHtml(o.status)}</span></div>${o.output?`<details><summary>Output</summary><pre>${escapeHtml(o.output)}</pre></details>`:''}</article>`).join('')||'<div class="empty-state">No recorded operations yet.</div>';
  }
  document.addEventListener('DOMContentLoaded',()=>{ensureDrawer();renderOperations();});
  if(document.body){ensureDrawer();renderOperations();}
})();
