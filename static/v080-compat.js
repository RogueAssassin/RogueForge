// RogueForge v0.8 UI compatibility/resilience layer.
(function () {
  const text = (selector, value) => { const node = document.querySelector(selector); if (node) node.textContent = value == null ? '—' : String(value); };
  renderStatus = function renderStatusV080Safe() {
    if (!state.status) return;
    const engine = state.status.engine || 'unknown';
    text('#engineName', `${engine} connected`); text('#engineDetail', state.status.socket || 'Protected'); text('#engineRuntime', engine); text('#engineInitial', engine.charAt(0).toUpperCase()); text('#engineVersion', state.status.version); text('#apiVersion', state.status.apiVersion); text('#socketPath', state.status.socket); text('#engineContext', state.status.context || 'default'); text('#stacksPath', state.status.stacksDir); text('#publicUrl', state.status.publicUrl || 'Not configured'); text('#appVersion', state.status.appVersion ? `v${state.status.appVersion}` : '—'); text('#stackNavCount', state.stacks?.length || 0); text('#containerNavCount', state.containers?.length || 0); text('#rfSidebarVersion', state.status.appVersion ? `v${state.status.appVersion}` : 'v0.8.x');
  };
  renderAll = function renderAllV080Safe() {
    try { renderStatus(); } catch (error) { console.error('RogueForge status render failed', error); }
    try { rfBranding(); } catch (error) { console.error('RogueForge branding render failed', error); }
    try { renderOverview(); } catch (error) { console.error('RogueForge overview render failed', error); const root=document.querySelector('#view-overview'); if(root)root.innerHTML=`<div class="empty-state">Overview failed to render: ${escapeHtml(error.message)}</div>`; }
    try { renderStacks(); } catch (error) { console.error('RogueForge stacks render failed', error); const root=document.querySelector('#stackGrid'); if(root)root.innerHTML=`<div class="empty-state">Stacks failed to render: ${escapeHtml(error.message)}</div>`; }
    try { renderContainers(); } catch (error) { console.error('RogueForge runtime render failed', error); const root=document.querySelector('#containerGrid'); if(root)root.innerHTML=`<div class="empty-state">Runtime failed to render: ${escapeHtml(error.message)}</div>`; }
  };
  const previousRenderAuth = renderAuth;
  renderAuth = function renderAuthV080Safe() { const button=document.querySelector('#accountButton'); if(!button)return; try{previousRenderAuth();}catch(error){console.error('RogueForge auth render failed',error);button.textContent=state.auth?.authenticated?String(state.auth.user||'A').slice(0,2).toUpperCase():'Sign in';} };
  const currentRenderStacks=renderStacks; renderStacks=function renderStacksV080Resilient(){const grid=document.querySelector('#stackGrid');if(!grid)return;return currentRenderStacks();};
  const currentRenderContainers=renderContainers; renderContainers=function renderRuntimeV080Resilient(){const grid=document.querySelector('#containerGrid');if(!grid)return;return currentRenderContainers();};
  window.addEventListener('error',event=>{if(String(event.message||'').includes('textContent'))console.error('RogueForge prevented a legacy DOM render failure from hiding workload data.',event.error||event.message);});

  // Load the canonical non-versioned quality layer last so it can safely extend the
  // stack renderer and icon resolver without adding another vNNN frontend file.
  const css=document.createElement('link');css.rel='stylesheet';css.href='/operations.css';document.head.appendChild(css);
  const script=document.createElement('script');script.src='/operations.js';script.defer=true;document.head.appendChild(script);
})();
