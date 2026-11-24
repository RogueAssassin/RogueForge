// RogueForge Updates page: which containers have a newer image available.
// Data comes from the built-in registry checker through /api/updates (administrator only).
pageMeta.updates = ['Image versions', 'Updates'];
const rfUpdates = { data: null, polling: 0, filter: 'all', query: '' };

function rfAgo(seconds) {
  const s = Math.max(0, Math.round(Date.now() / 1000 - seconds));
  if (s < 60) return 'just now';
  if (s < 3600) return Math.round(s / 60) + ' min ago';
  if (s < 86400) return Math.round(s / 3600) + ' h ago';
  return Math.round(s / 86400) + ' d ago';
}
function rfIn(seconds) {
  const s = Math.round(seconds - Date.now() / 1000);
  if (s <= 60) return 'shortly';
  return 'in ' + (s < 5400 ? Math.round(s / 60) + ' min' : Math.round(s / 3600) + ' h');
}

function rfUpdateKind(item) {
  if (item.error) return 'failed';
  if (item.updateAvailable) return 'updates';
  if (item.note) return 'skipped';
  return 'current';
}
const rfUpdateRank = { updates: 0, failed: 1, skipped: 2, current: 3 };

function rfUpdateBadge(item) {
  if (item.error) return '<span class="rf-upd-badge err" title="' + attr(item.error) + '">Check failed</span>';
  if (item.updateAvailable) {
    const label = item.kind === 'digest' ? 'new build' : (item.semverDiff || 'update');
    return '<span class="rf-upd-badge new">' + escapeHtml(label) + '</span>';
  }
  if (item.note) return '<span class="rf-upd-badge skip" title="' + attr(item.note) + '">Not checked</span>';
  return '<span class="rf-upd-badge ok">Up to date</span>';
}

function rfUpdateAction(item) {
  if (!item.updateAvailable) return '';
  if (item.self) return '<small class="rf-upd-hint">Update from the host: ./update.sh latest</small>';
  if (!item.stack) return '';
  const s = attr(item.stack);
  // A pinned version tag only changes when the Compose file changes; a moving tag only needs a pull.
  if (item.kind === 'tag') return '<button class="small-button" data-edit-stack="' + s + '" title="Set the image tag to ' + attr(item.latestTag) + '">Edit Compose</button>';
  return '<button class="small-button accent" data-upd-stack="' + s + '">Update</button>';
}

function rfUpdateRow(item) {
  const image = [item.registry && item.registry !== 'docker.io' ? item.registry : '', item.repository || item.image].filter(Boolean).join('/');
  let versions;
  if (item.updateAvailable && item.kind === 'tag') versions = escapeHtml(item.currentTag) + ' → <b>' + escapeHtml(item.latestTag) + '</b>';
  else if (item.updateAvailable) versions = escapeHtml(item.currentTag) + ' <b>(rebuilt)</b>';
  else versions = escapeHtml(item.currentTag || '—');
  const detail = item.error || item.note;
  return '<div class="rf-upd-row' + (item.updateAvailable ? ' has-update' : '') + '"><div><strong>' + escapeHtml(item.name) + '</strong><small>' +
    escapeHtml(item.stack ? item.stack + ' · ' : '') + escapeHtml(image) + '</small></div><div class="rf-upd-ver">' + versions +
    (detail && !item.updateAvailable ? '<small>' + escapeHtml(detail) + '</small>' : '') + '</div><div class="rf-upd-side">' + rfUpdateAction(item) + rfUpdateBadge(item) + '</div></div>';
}

function rfUpdateVisible(items) {
  const q = rfUpdates.query.trim().toLowerCase();
  return items
    .filter(i => (rfUpdates.filter === 'all' || rfUpdateKind(i) === rfUpdates.filter) &&
      (!q || [i.name, i.stack, i.image, i.repository].some(v => String(v || '').toLowerCase().includes(q))))
    .sort((a, b) => rfUpdateRank[rfUpdateKind(a)] - rfUpdateRank[rfUpdateKind(b)] || String(a.name).localeCompare(String(b.name)));
}

function renderUpdateTools(d) {
  const tools = $('#updatesTools'), chips = $('#updatesChips');
  if (!tools || !chips) return;
  const show = !!(d && d.enabled && d.checkedAt);
  tools.hidden = !show;
  if (!show) return;
  const n = { all: d.items.length, updates: 0, failed: 0, skipped: 0 };
  d.items.forEach(i => { const k = rfUpdateKind(i); if (k in n) n[k]++; });
  const defs = [['all', 'All'], ['updates', 'Updates'], ['failed', 'Failed'], ['skipped', 'Not checked']];
  chips.innerHTML = defs.filter(([k]) => k === 'all' || k === 'updates' || n[k] || rfUpdates.filter === k)
    .map(([k, label]) => '<button type="button" class="rf-upd-chip' + (rfUpdates.filter === k ? ' active' : '') + '" data-upd-filter="' + k + '">' + label + ' <b>' + n[k] + '</b></button>').join('');
}

function renderUpdates() {
  const d = rfUpdates.data, box = $('#updatesBody'), nav = $('#updateNavCount');
  if (nav) {
    nav.textContent = d && d.enabled && d.checkedAt ? String(d.updates) : '—';
    nav.classList.toggle('rf-upd-alert', !!(d && d.enabled && d.updates));
  }
  const check = $('#updatesCheck'); if (check) check.disabled = !!(d && (d.checking || !d.enabled));
  renderUpdateTools(d);
  if (!box) return;
  if (!d) { box.innerHTML = '<div class="empty-state">Loading update status…</div>'; return; }
  if (!d.enabled) { box.innerHTML = '<div class="empty-state">' + escapeHtml(d.message || 'Update checking is disabled.') + '</div>'; return; }
  const warn = d.error ? '<div class="rf-upd-warn">' + escapeHtml(d.error) + '</div>' : '';
  if (!d.checkedAt) { box.innerHTML = warn + '<div class="empty-state">' + (d.checking ? 'Checking registries…' : 'No check has finished yet. Press Check now.') + '</div>'; return; }
  let when = 'Checked ' + rfAgo(d.checkedAt);
  if (d.checking) when += ' · checking again…';
  else if (d.nextCheckAt) when += ' · next check ' + rfIn(d.nextCheckAt);
  else if (!d.intervalHours) when += ' · automatic checks are off';
  const failed = d.items.filter(i => i.error).length;
  const head = d.updates
    ? '<strong>' + d.updates + '</strong> of ' + d.total + ' containers have an update'
    : '<strong>All ' + d.total + '</strong> containers are up to date';
  const rows = rfUpdateVisible(d.items);
  box.innerHTML = warn + '<div class="rf-upd-summary' + (d.updates ? ' has-update' : '') + '">' + head +
    (failed ? '<span class="rf-upd-fail">' + failed + ' could not be checked</span>' : '') +
    '<small title="' + attr(new Date(d.checkedAt * 1000).toLocaleString()) + '">' + escapeHtml(when) + '</small></div>' +
    (rows.map(rfUpdateRow).join('') || '<div class="empty-state">' + (d.items.length ? 'No containers match this filter.' : 'No containers found.') + '</div>');
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

// Pull and recreate a stack through the normal verified update flow, then re-check.
async function rfUpdateFromPage(stack) {
  if (typeof rfUpdateStack !== 'function') return;
  await rfUpdateStack(stack);
  await checkUpdatesNow();
}

const rfPreviousSetView = setView;
setView = function setViewWithUpdates(name) {
  rfPreviousSetView(name);
  if (name === 'updates' && state.auth.authenticated) loadUpdates();
};
document.addEventListener('click', event => {
  if (event.target.closest('#updatesRefresh')) loadUpdates();
  if (event.target.closest('#updatesCheck')) checkUpdatesNow();
  const chip = event.target.closest('[data-upd-filter]');
  if (chip) { rfUpdates.filter = chip.dataset.updFilter; renderUpdates(); }
  const upd = event.target.closest('[data-upd-stack]');
  if (upd) rfUpdateFromPage(upd.dataset.updStack);
});
document.addEventListener('input', event => {
  if (event.target.id === 'updatesSearch') { rfUpdates.query = event.target.value; renderUpdates(); }
});
// Fill the sidebar count once after sign-in, without opening the page (stops after ~1 minute).
let rfUpdateTries = 0;
const rfUpdateTimer = setInterval(() => {
  if (rfUpdates.data || ++rfUpdateTries > 15) { clearInterval(rfUpdateTimer); return; }
  if (state.auth.authenticated) loadUpdates();
}, 4000);
if (location.hash === '#updates') setView('updates');
