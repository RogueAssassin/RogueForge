// RogueForge v0.8.0 compatibility/resilience layer.
// The v0.8 UI replaces parts of the legacy DOM. Treat legacy status nodes as
// optional so a refresh can never abort because an old element no longer exists.
(function () {
  const text = (selector, value) => {
    const node = document.querySelector(selector);
    if (node) node.textContent = value == null ? '—' : String(value);
  };

  const title = (selector, value) => {
    const node = document.querySelector(selector);
    if (node) node.title = value == null ? '' : String(value);
  };

  renderStatus = function renderStatusV080Safe() {
    if (!state.status) return;
    const engine = state.status.engine || 'unknown';
    text('#engineName', `${engine} connected`);
    text('#engineDetail', state.status.socket || 'Protected');
    text('#engineRuntime', engine);
    text('#engineInitial', engine.charAt(0).toUpperCase());
    text('#engineVersion', state.status.version);
    text('#apiVersion', state.status.apiVersion);
    text('#socketPath', state.status.socket);
    text('#engineContext', state.status.context || 'default');
    text('#stacksPath', state.status.stacksDir);
    text('#publicUrl', state.status.publicUrl || 'Not configured');
    text('#appVersion', state.status.appVersion ? `v${state.status.appVersion}` : '—');
    text('#stackNavCount', state.stacks?.length || 0);
    text('#containerNavCount', state.containers?.length || 0);
    text('#rfSidebarVersion', state.status.appVersion ? `v${state.status.appVersion}` : 'v0.8.0');
  };

  // Render each v0.8 surface exactly once. Do not call the old renderAll first,
  // because it can target markup that v0.8 intentionally replaced.
  renderAll = function renderAllV080Safe() {
    try { renderStatus(); } catch (error) { console.error('RogueForge status render failed', error); }
    try { rfBranding(); } catch (error) { console.error('RogueForge branding render failed', error); }
    try { renderOverview(); } catch (error) {
      console.error('RogueForge overview render failed', error);
      const root = document.querySelector('#view-overview');
      if (root) root.innerHTML = `<div class="empty-state">Overview failed to render: ${escapeHtml(error.message)}</div>`;
    }
    try { renderStacks(); } catch (error) {
      console.error('RogueForge stacks render failed', error);
      const root = document.querySelector('#stackGrid');
      if (root) root.innerHTML = `<div class="empty-state">Stacks failed to render: ${escapeHtml(error.message)}</div>`;
    }
    try { renderContainers(); } catch (error) {
      console.error('RogueForge runtime render failed', error);
      const root = document.querySelector('#containerGrid');
      if (root) root.innerHTML = `<div class="empty-state">Runtime failed to render: ${escapeHtml(error.message)}</div>`;
    }
  };

  // Harden auth rendering too: account UI is useful but should never prevent
  // infrastructure data from appearing if the header changes in future themes.
  const previousRenderAuth = renderAuth;
  renderAuth = function renderAuthV080Safe() {
    const button = document.querySelector('#accountButton');
    if (!button) return;
    try { previousRenderAuth(); }
    catch (error) {
      console.error('RogueForge auth render failed', error);
      button.textContent = state.auth?.authenticated ? String(state.auth.user || 'A').slice(0, 2).toUpperCase() : 'Sign in';
    }
  };

  // A missing filter/input should simply mean an empty query, not a dead page.
  const currentRenderStacks = renderStacks;
  renderStacks = function renderStacksV080Resilient() {
    const grid = document.querySelector('#stackGrid');
    if (!grid) return;
    return currentRenderStacks();
  };

  const currentRenderContainers = renderContainers;
  renderContainers = function renderRuntimeV080Resilient() {
    const grid = document.querySelector('#containerGrid');
    if (!grid) return;
    return currentRenderContainers();
  };

  window.addEventListener('error', event => {
    if (String(event.message || '').includes('textContent')) {
      console.error('RogueForge prevented a legacy DOM render failure from hiding workload data.', event.error || event.message);
    }
  });
})();
