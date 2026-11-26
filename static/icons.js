// RogueForge icon set: one stroke style, inline SVG, no external requests.
// Icons are applied by selector so every renderer (and later re-render) gets them from one place.
(() => {
  const PATHS = {
    home: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    layers: '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/>',
    box: '<path d="M21 8 12 3 3 8v8l9 5 9-5V8Z"/><path d="m3 8 9 5 9-5M12 13v8"/>',
    image: '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/>',
    database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    network: '<rect x="9" y="3" width="6" height="6" rx="1"/><rect x="3" y="15" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/><path d="M12 9v3M6 15v-3h12v3"/>',
    update: '<circle cx="12" cy="12" r="9"/><path d="m8 12 4-4 4 4M12 8v8"/>',
    settings: '<path d="M4 6h9M19 6h1M4 12h3M13 12h7M4 18h11"/><circle cx="16" cy="6" r="2.5"/><circle cx="10" cy="12" r="2.5"/><circle cx="18" cy="18" r="2.5"/>',
    play: '<path d="M7 4.5v15l12-7.5-12-7.5Z"/>',
    stop: '<rect x="6" y="6" width="12" height="12" rx="2"/>',
    pause: '<path d="M9 5v14M15 5v14"/>',
    restart: '<path d="M20 11a8 8 0 1 0-2.3 6.3"/><path d="M20 4v7h-7"/>',
    refresh: '<path d="M3 12a9 9 0 0 1 15.5-6.2L21 8M21 3v5h-5M21 12a9 9 0 0 1-15.5 6.2L3 16M3 21v-5h5"/>',
    download: '<path d="M12 4v11m-5-4 5 5 5-5M4 20h16"/>',
    rebuild: '<path d="M14.7 6.3a4 4 0 0 0-5 5L3 18v3h3l6.7-6.7a4 4 0 0 0 5-5L15 12l-3-3 2.7-2.7Z"/>',
    edit: '<path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z"/>',
    logs: '<path d="M5 3h10l4 4v14H5V3ZM9 11h6M9 15h6"/>',
    terminal: '<path d="m5 7 5 5-5 5M12 19h7"/>',
    trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v5M14 11v5"/>',
    close: '<path d="M6 6l12 12M18 6 6 18"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    activity: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    chevron: '<path d="m6 9 6 6 6-6"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    checkAll: '<path d="M3 5h18v14H3zM8 12l3 3 5-6"/>',
    heart: '<path d="M12 20s-8-4.6-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 9c0 6.4-8 11-8 11Z"/>',
    eye: '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
    send: '<path d="M21 3 10 14M21 3l-7 18-4-7-7-4 18-7Z"/>',
  };
  const icon = (name, size = 16) =>
    '<svg class="rf-i" viewBox="0 0 24 24" width="' + size + '" height="' + size + '" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + (PATHS[name] || '') + '</svg>';
  window.rfIcon = icon;

  // Replace the element's content with an icon (icon-only controls).
  const ONLY = [
    ['#menuButton', 'menu', 'Open menu', 19], ['#refreshButton', 'refresh', 'Refresh', 17], ['.close-button', 'close', 'Close', 17],
    ['.filter > span:first-child', 'search', '', 15],
    ['.nav-item[data-view="overview"] .nav-icon', 'home'], ['.nav-item[data-view="stacks"] .nav-icon', 'layers'],
    ['.nav-item[data-view="containers"] .nav-icon', 'box'], ['.nav-item[data-view="images"] .nav-icon', 'image'],
    ['.nav-item[data-view="volumes"] .nav-icon', 'database'], ['.nav-item[data-view="networks"] .nav-icon', 'network'],
    ['.nav-item[data-view="updates"] .nav-icon', 'update'], ['.nav-item[data-view="settings"] .nav-icon', 'settings'],
    ['.rf-summary-card.purple .rf-summary-icon', 'layers', '', 20], ['.rf-summary-card.cyan .rf-summary-icon', 'box', '', 20],
    ['.rf-summary-card.green .rf-summary-icon', 'play', '', 20], ['.rf-summary-card.red .rf-summary-icon', 'stop', '', 20],
    ['.rf-summary-card.teal .rf-summary-icon', 'heart', '', 20],
    ['.rf-quick[data-go="stacks"] .rf-quick-icon', 'layers', '', 18], ['#rfUpdateAll .rf-quick-icon', 'update', '', 18],
    ['.rf-quick[data-go="containers"] .rf-quick-icon', 'box', '', 18], ['.rf-quick[data-go="settings"] .rf-quick-icon', 'settings', '', 18],
    ['#rfDiscovery .rf-quick-icon', 'search', '', 18],
    ['#imageGrid .resource-icon', 'image', '', 20], ['#volumeGrid .resource-icon', 'database', '', 20], ['#networkGrid .resource-icon', 'network', '', 20],
  ];
  // Put an icon before the label (or after it, for disclosure toggles).
  const actions = { start: 'play', stop: 'stop', restart: 'restart', pull: 'download', update: 'update', recreate: 'rebuild', remove: 'trash' };
  const LEAD = [];
  ['data-stack-action', 'data-container-action', 'data-bulk-action'].forEach(a => Object.entries(actions).forEach(([k, v]) => LEAD.push(['button[' + a + '="' + k + '"]', v])));
  LEAD.push(['button[data-rf-stack-update]', 'update'], ['button[data-upd-stack]', 'update'], ['#updateAllContainers', 'update'],
    ['button[data-rf-config]', 'edit'], ['button[data-edit-stack]', 'edit'], ['button[data-live-logs]', 'activity'], ['button[data-terminal]', 'terminal'],
    ['button[data-resource-refresh]', 'refresh'], ['#updatesRefresh', 'refresh'], ['#rfRefreshOverview', 'refresh'], ['#updatesCheck', 'search'],
    ['#imagesPruneDangling', 'trash'], ['#imagesPruneUnused', 'trash'], ['#volumesPruneUnused', 'trash'],
    ['button[data-image-remove]', 'trash'], ['button[data-volume-remove]', 'trash'], ['#saveCompose', 'check'],
    ['#pauseLiveLogs', 'pause'], ['#clearLiveLogs', 'trash'], ['#downloadLiveLogs', 'download'], ['#terminalSend', 'send'],
    ['#selectVisibleContainers', 'checkAll'], ['button[data-go-stack]', 'arrow'], ['.account-button:not(.authenticated)', 'user'],
    ['button[data-container-action="check-update"]', 'refresh'], ['button[data-inspect]', 'eye'], ['button[data-logs]', 'logs'],
    ['button[data-rf-expand]', 'chevron', true]);
  const GLYPHS = /^[\s↻⇩⌂◇▣◉⌘⇪⚙☰⌕⌁▶■□▷♡⬡▦✓]+|[\s▾▴]+$/g;

  function stripGlyphs(el) {
    el.childNodes.forEach(node => {
      if (node.nodeType === 3) { const next = node.textContent.replace(GLYPHS, ''); if (next !== node.textContent) node.textContent = next; }
    });
  }
  const has = el => el.querySelector(':scope > svg.rf-i');

  function decorate() {
    ONLY.forEach(([selector, name, label, size]) => document.querySelectorAll(selector).forEach(el => {
      if (has(el)) return;
      el.innerHTML = icon(name, size || 17);
      if (label && !el.getAttribute('aria-label')) el.setAttribute('aria-label', label);
    }));
    LEAD.forEach(([selector, name, trailing]) => document.querySelectorAll(selector).forEach(el => {
      if (has(el)) return;
      stripGlyphs(el);
      el.classList.add('rf-has-icon');
      // The runtime table shows icons only; keep the label for tooltips and screen readers.
      if (el.closest('.container-table')) { const label = el.textContent.trim(); el.title = label; el.setAttribute('aria-label', label); }
      el.insertAdjacentHTML(trailing ? 'beforeend' : 'afterbegin', icon(name, 14));
    }));
    const activity = document.getElementById('rfOperationsButton');
    if (activity && !has(activity)) {
      stripGlyphs(activity);
      activity.insertAdjacentHTML('afterbegin', icon('activity', 17));
      activity.setAttribute('aria-label', 'Operations history');
    }
  }

  let queued = false;
  const schedule = () => { if (!queued) { queued = true; queueMicrotask(() => { queued = false; decorate(); }); } };
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener('DOMContentLoaded', decorate);
  schedule();
})();
