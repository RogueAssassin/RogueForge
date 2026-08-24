// RogueForge v0.6.0 container controls.
// Loaded after app.js so it can extend the stable UI without replacing core behaviour.

function containerCapabilities(container) {
  const running = container.state === "running";
  const protectedSelf = !!container.selfProtected;
  return {
    canStart: !protectedSelf && !running,
    canStop: !protectedSelf && running,
    canRestart: !protectedSelf && running,
    canUpdate: !protectedSelf,
    canRecreate: !protectedSelf && !!container.composeManaged,
    canRemove: !protectedSelf,
    canInspect: true,
    canLogs: true,
  };
}

function containerActionButton(label, action, container, className = "") {
  return `<button class="small-button ${className}" data-container-action="${action}" data-container="${container.id}" data-name="${attr(container.name)}">${label}</button>`;
}

renderContainers = function renderContainersV060() {
  const query = $("#containerSearch").value.trim().toLowerCase();
  const containers = state.containers.filter(item => [item.name, item.image, item.state, item.project, item.service].some(value => String(value || "").toLowerCase().includes(query)));
  $("#containerGrid").innerHTML = `<div class="container-head"><span>Container</span><span>Image / service</span><span>State</span><span>Ports</span><span>Actions</span></div>` + containers.map(container => {
    const caps = containerCapabilities(container);
    const service = container.service ? `${container.project} / ${container.service}` : (container.project && container.project !== "standalone" ? container.project : "standalone");
    let actions = "";
    if (caps.canStart) actions += containerActionButton("Start", "start", container, "accent");
    if (caps.canStop) actions += containerActionButton("Stop", "stop", container);
    if (caps.canRestart) actions += containerActionButton("Restart", "restart", container);
    if (caps.canUpdate) actions += containerActionButton("Update", "update", container, "accent");
    if (caps.canRecreate) actions += containerActionButton("Recreate", "recreate", container);
    actions += `<button class="small-button" data-inspect="${container.id}" data-name="${attr(container.name)}">Inspect</button>`;
    actions += `<button class="small-button accent" data-logs="${container.id}" data-name="${attr(container.name)}">Logs</button>`;
    if (caps.canRemove) actions += containerActionButton("Remove", "remove", container, "danger-action");
    if (container.selfProtected) actions = `<span class="service-count" title="RogueForge protects its own container from in-app lifecycle operations">Self-protected</span>` + actions;
    return `
      <div class="container-row container-row-v060">
        <div class="container-name">${serviceLogo(container.name)}<div><strong>${escapeHtml(container.name)}</strong><small>${escapeHtml(container.id)}</small></div></div>
        <div class="container-image-block"><span class="image-name" title="${attr(container.image)}">${escapeHtml(container.image)}</span><small>${escapeHtml(service)}</small></div>
        ${stateBadge(container.state)}
        <span class="port-list">${escapeHtml(formatPorts(container.ports))}</span>
        <div class="container-actions container-actions-v060">${actions}</div>
      </div>`;
  }).join("") || '<div class="empty-state">No containers match this filter.</div>';
};

containerAction = async function containerActionV060(id, action) {
  if (!ensureAuthenticated()) return;
  const container = state.containers.find(item => item.id === id) || { name: "container" };
  const labels = { start: "Start", stop: "Stop", restart: "Restart", update: "Update", recreate: "Recreate", remove: "Remove" };
  const prompts = {
    start: `Start ${container.name}?`,
    stop: `Stop ${container.name}? The container will remain available to start again.`,
    restart: `Restart ${container.name}? It may be briefly unavailable.`,
    update: container.composeManaged ? `Pull the latest image for ${container.name} and recreate only its Compose service?` : `Pull the latest image for ${container.name}? Standalone containers are not automatically recreated.`,
    recreate: `Force-recreate only ${container.name} from its Compose service definition?`,
    remove: container.composeManaged ? `Remove ${container.name}? The Compose service definition is kept and can be started again later.` : `Permanently remove ${container.name}?`,
  };
  const destructive = ["stop", "restart", "update", "recreate", "remove"].includes(action);
  if (destructive && !await confirmAction(`${labels[action] || action} container?`, prompts[action] || "Continue with this container action?", labels[action] || "Continue")) return;
  try {
    toast(`${labels[action] || action} started for ${container.name}`);
    const result = await api(`/api/containers/${id}/${action}`, protectedOptions({ method: "POST" }));
    if (result.output) console.info(result.output);
    if (result.message) toast(result.message, "success");
    else toast(`${container.name}: ${action} completed`);
    await load({ quiet: true });
  } catch (error) {
    toast(error.message, "error");
  }
};

async function inspectContainer(id, name) {
  if (!ensureAuthenticated()) return;
  try {
    const data = await api(`/api/containers/${id}/inspect`);
    const lines = [
      `Name: ${data.name}`,
      `ID: ${data.id}`,
      `Image: ${data.image}`,
      `Image ID: ${data.imageId || "—"}`,
      `State: ${data.status || "—"}`,
      `Created: ${data.created || "—"}`,
      `Started: ${data.startedAt || "—"}`,
      `Finished: ${data.finishedAt || "—"}`,
      `Restart count: ${data.restartCount ?? 0}`,
      `Compose project: ${data.project || "standalone"}`,
      `Compose service: ${data.service || "—"}`,
      `Networks: ${(data.networks || []).join(", ") || "—"}`,
      `Command: ${(data.command || []).join(" ") || "—"}`,
      "",
      "Mounts:",
      ...(data.mounts || []).map(m => `  ${m.source || "—"} -> ${m.destination || "—"} (${m.type || "mount"}${m.rw === false ? ", read-only" : ""})`),
    ];
    $("#logsTitle").textContent = `${name} · Inspect`;
    $("#logText").textContent = lines.join("\n");
    $("#logsDialog").showModal();
  } catch (error) {
    toast(error.message, "error");
  }
}

document.addEventListener("click", event => {
  const inspect = event.target.closest("[data-inspect]");
  if (inspect) inspectContainer(inspect.dataset.inspect, inspect.dataset.name);
});

// Re-render immediately if the base application has already loaded data.
if (state?.containers?.length) renderContainers();
