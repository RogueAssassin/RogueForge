// RogueForge cleanup: remove unused images and volumes from their pages.
// The server re-checks usage on every request and runs the engine without --force.
function rfCleanDialog() {
  if ($('#rfCleanDialog')) return $('#rfCleanDialog');
  document.body.insertAdjacentHTML('beforeend', '<dialog id="rfCleanDialog"><div class="modal"><header><div><p class="eyebrow" id="rfCleanEyebrow">Cleanup</p><h2 id="rfCleanTitle"></h2></div><button class="close-button" type="button" id="rfCleanClose">×</button></header>' +
    '<div class="rf-clean-body"><p id="rfCleanMessage"></p><ul class="rf-clean-list" id="rfCleanList"></ul><label class="rf-clean-confirm" id="rfCleanConfirmRow"><span>Type <b id="rfCleanWord"></b> to confirm</span><input id="rfCleanInput" autocomplete="off" spellcheck="false"></label></div>' +
    '<footer><button class="button secondary" type="button" id="rfCleanCancel">Cancel</button><button class="button danger" type="button" id="rfCleanOk">Remove</button></footer></div></dialog>');
  return $('#rfCleanDialog');
}

// Resolves true when the user confirms. `word` (optional) must be typed first.
function rfCleanConfirm({ eyebrow, title, message, items = [], word = '', button = 'Remove' }) {
  const dialog = rfCleanDialog(), input = $('#rfCleanInput'), ok = $('#rfCleanOk');
  $('#rfCleanEyebrow').textContent = eyebrow; $('#rfCleanTitle').textContent = title; $('#rfCleanMessage').textContent = message;
  $('#rfCleanList').innerHTML = items.slice(0, 12).map(x => '<li>' + escapeHtml(x) + '</li>').join('') + (items.length > 12 ? '<li>and ' + (items.length - 12) + ' more</li>' : '');
  $('#rfCleanConfirmRow').hidden = !word; $('#rfCleanWord').textContent = word; input.value = ''; ok.textContent = button; ok.disabled = !!word;
  return new Promise(resolve => {
    const finish = value => { dialog.close(); ok.onclick = cancel.onclick = close.onclick = input.oninput = null; resolve(value); };
    const cancel = $('#rfCleanCancel'), close = $('#rfCleanClose');
    ok.onclick = () => finish(true); cancel.onclick = close.onclick = () => finish(false);
    input.oninput = () => { ok.disabled = input.value.trim() !== word; };
    dialog.oncancel = () => finish(false);
    dialog.showModal(); (word ? input : cancel).focus();
  });
}

async function rfCleanRun(url, body, kind) {
  let r;
  try { r = await api(url, protectedOptions({ method: 'POST', body: JSON.stringify(body) })); }
  catch (error) { toast(error.message, 'error'); return; }
  const n = r.removed.length, size = r.reclaimedBytes ? ' (' + formatBytes(r.reclaimedBytes) + ' freed)' : '';
  if (n) toast('Removed ' + n + ' ' + kind + (n === 1 ? '' : 's') + size);
  if (r.failed.length) toast(r.failed.length + ' could not be removed: ' + r.failed[0].ref + ' — ' + r.failed[0].error, 'error');
  else if (!n) toast('Nothing was removed' + (r.skipped.length ? ': ' + r.skipped[0].reason : ''), 'error');
  await loadResource(kind + 's', { force: true });
}

async function rfRemoveImage(id, tag, ref) {
  if (!ensureAuthenticated()) return;
  if (!await rfCleanConfirm({ eyebrow: 'Images', title: 'Remove image?', message: 'The image is not used by any container. It can be pulled again later.', items: [ref] })) return;
  await rfCleanRun('/api/images/remove', { id, tag }, 'image');
}

async function rfPruneImages(mode) {
  if (!ensureAuthenticated()) return;
  const rows = (state.images || []).filter(x => !x.inUse && (mode === 'unused' || x.repository === '<none>' || x.tag === '<none>'));
  if (!rows.length) { toast(mode === 'unused' ? 'No unused images.' : 'No dangling images.'); return; }
  const items = rows.map(x => (x.repository === '<none>' || x.tag === '<none>') ? '<untagged> ' + (x.shortId || '') : x.repository + ':' + x.tag);
  const text = mode === 'unused'
    ? 'Removes every image that no container (running or stopped) uses. Images for stacks that are currently stopped or taken down are included and will be pulled again when you start them.'
    : 'Removes untagged leftovers that no container uses. This is the safe everyday cleanup.';
  if (!await rfCleanConfirm({ eyebrow: 'Images', title: 'Remove ' + rows.length + ' ' + (mode === 'unused' ? 'unused' : 'dangling') + ' image' + (rows.length === 1 ? '' : 's') + '?', message: text, items })) return;
  await rfCleanRun('/api/images/prune', { mode }, 'image');
}

async function rfRemoveVolumes(names) {
  if (!ensureAuthenticated() || !names.length) return;
  const many = names.length > 1;
  const ok = await rfCleanConfirm({
    eyebrow: 'Volumes', title: 'Permanently delete ' + (many ? names.length + ' volumes' : 'this volume') + '?',
    message: 'Volumes hold data (databases, settings, downloads). Deleting is permanent and cannot be undone. A volume shows as unused when no container mounts it, which also happens when its stack is taken down but you still want the data.',
    items: names, word: many ? 'DELETE' : names[0], button: 'Delete permanently',
  });
  if (ok) await rfCleanRun('/api/volumes/remove', { names }, 'volume');
}

document.addEventListener('click', event => {
  const img = event.target.closest('[data-image-remove]');
  if (img) return rfRemoveImage(img.dataset.imageRemove, img.dataset.imageTag, img.dataset.imageRef);
  const vol = event.target.closest('[data-volume-remove]');
  if (vol) return rfRemoveVolumes([vol.dataset.volumeRemove]);
  if (event.target.closest('#imagesPruneDangling')) return rfPruneImages('dangling');
  if (event.target.closest('#imagesPruneUnused')) return rfPruneImages('unused');
  if (event.target.closest('#volumesPruneUnused')) {
    const names = (state.volumes || []).filter(x => !x.inUse).map(x => x.name);
    if (names.length) rfRemoveVolumes(names); else toast('No unused volumes.');
  }
});
