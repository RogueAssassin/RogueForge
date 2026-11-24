// RogueForge Updates page: which containers have a newer image available.
// Data comes from the built-in registry checker through /api/updates (administrator only).
pageMeta.updates = ['Image versions', 'Updates'];
const rfUpdates = { data: null, polling: 0 };

function rfUpdateBadge(item) {
  if (item.error) return '<span class="rf-upd-badge err" title="' + attr(item.error) + '">Check failed</span>';
  if (item.updateAvailable) {
    const label = item.kind === 'digest' ? 'new build' : (item.semverDiff || 'update');
    return '<span class="rf-upd-badge new">' + escapeHtml(label) + '</span>';
  }
  if (item.note) return '<span class="rf-upd-badge skip" title="' + attr(item.note) + '">Not checked</span>';
  return '<span class="rf-upd-badge ok">Up to date</span>';
}

function rfUpdateRow(item) {
  const image = [item.registry && item.registry !== 'docker.io' ? item.registry : '', item.repository || item.image].filter(Boolean).join('/');
  let versions;
  if (item.updateAvailable && item.kind === 'tag') versions = escapeHtml(item.currentTag) + ' → <b>' + escapeHtml(item.latestTag) + '</b>';
  else if (item.updateAvailable) versions = escapeHtml(item.currentTag) + ' <b>(rebuilt)</b>';
  else versions = escapeHtml(item.currentTag || '—');
  const detail = item.error || item.note;
  return '<div class="rf-upd-row"><div><strong>' + escapeHtml(item.name) + '</strong><small>' +
    escapeHtml(item.stack ? item.stack + ' · ' : '') + escapeHtml(image) + '</small></div><div class="rf-upd-ver">' + versions +
    (detail && !item.updateAvailable ? '<small>' + escapeHtml(detail) + '</small>' : '') + '</div>' + rfUpdateBadge(item) + '</div>';
}

function renderUpdates() {
  const d = rfUpdates.data, box = $('#updatesBody'), nav = $('#updateNavCount');
  if (nav) {
    nav.textContent = d && d.enabled && d.checkedAt ? String(d.updates) : '—';
    nav.classList.toggle('rf-upd-alert', !!(d && d.enabled && d.updates));
  }
  const check = $('#updatesCheck'); if (check) check.disabled = !!(d && (d.checking || !d.enabled));
  if (!box) return;
  if (!d) { box.innerHTML = '<div class="empty-state">Loading update status…</div>'; return; }
  if (!d.enabled) { box.innerHTML = '<div class="empty-state">' + escapeHtml(d.message || 'Update checking is disabled.') + '</div>'; return; }
  const warn = d.error ? '<div class="rf-upd-warn">' + escapeHtml(d.error) + '</div>' : '';
  if (!d.checkedAt) { box.innerHTML = warn + '<div class="empty-state">' + (d.checking ? 'Checking registries…' : 'No check has finished yet. Press Check now.') + '</div>'; return; }
  const when = 'Last checked ' + new Date(d.checkedAt * 1000).toLocaleString() + (d.checking ? ' · checking again…' : '');
  box.innerHTML = warn + '<div class="rf-upd-summary"><strong>' + d.updates + '</strong> of ' + d.total +
    ' containers have an update<small>' + escapeHtml(when) + '</small></div>' +
    (d.items.map(rfUpdateRow).join('') || '<div class="empty-state">No containers found.</div>');
}

async function loadUpdates() {
  try { rfUpdates.data = await api('/api/updates'); }
  catch (error) { rfUpdates.data = null; const box = $('#updatesBody'); if (box) box.innerHTML = '<div class="empty-state">' + escapeHtml(error.message) + '</div>'; return; }
  renderUpdates();
  // Follow a running scan until it finishes (bounded, 2 s apart).
  if (rfUpdates.data.checking && rfUpdates.polling < 90) { rfUpdates.polling++; setTimeout(loadUpdates, 2000); } else rfUpdates.polling = 0;
}

async function checkUpdatesNow() {
  if (!ensureAuthenticated()) return;
  try { rfUpdates.data = await api('/api/updates/check', protectedOptions({ method: 'POST' })); renderUpdates(); rfUpdates.polling = 0; setTimeout(loadUpdates, 1500); }
  catch (error) { toast(error.message, 'error'); }
}

const rfPreviousSetView = setView;
setView = function setViewWithUpdates(name) {
  rfPreviousSetView(name);
  if (name === 'updates' && state.auth.authenticated) loadUpdates();
};
document.addEventListener('click', event => {
  if (event.target.closest('#updatesRefresh')) loadUpdates();
  if (event.target.closest('#updatesCheck')) checkUpdatesNow();
});
// Fill the sidebar count once after sign-in, without opening the page (stops after ~1 minute).
let rfUpdateTries = 0;
const rfUpdateTimer = setInterval(() => {
  if (rfUpdates.data || ++rfUpdateTries > 15) { clearInterval(rfUpdateTimer); return; }
  if (state.auth.authenticated) loadUpdates();
}, 4000);
if (location.hash === '#updates') setView('updates');
