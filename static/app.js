const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const state = { status: null, stacks: [], containers: [], currentStack: null, loading: false, auth: { configured: false, authenticated: false, user: null, csrf: null } };
const pageMeta = {
  overview: ["Command centre", "Overview"],
  stacks: ["Compose workloads", "Stacks"],
  containers: ["Runtime inventory", "Containers"],
  settings: ["RogueForge", "Settings"]
};

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "content-type": "application/json" }, ...options });
  let data;
  try { data = await response.json(); } catch { data = {}; }
  if (response.status === 401 && !path.endsWith("/auth/login")) {
    state.auth = { configured: true, authenticated: false, user: null, csrf: null };
    renderAuth();
  }
  if (!response.ok) throw new Error(data.error || data.output || `Request failed (${response.status})`);
  return data;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function attr(value) { return escapeHtml(value).replace(/`/g, "&#96;"); }

function toast(message, type = "success") {
  const item = document.createElement("div");
  item.className = `toast ${type}`;
  item.textContent = message;
  $("#toasts").append(item);
  setTimeout(() => item.remove(), 4200);
}

function protectedOptions(options = {}) {
  return { ...options, headers: { "content-type": "application/json", "x-csrf-token": state.auth.csrf || "", ...(options.headers || {}) } };
}

function ensureAuthenticated() {
  if (state.auth.authenticated) return true;
  const authInfo = state.auth.auth || {};
  $("#loginError").textContent = state.auth.configured ? "" : (authInfo.exists ? "Administrator credentials could not be read or validated." : "No administrator account has been provisioned yet.");
  $("#loginDialog").showModal();
  setTimeout(() => $("#loginUsername").focus(), 50);
  return false;
}

function renderAuth() {
  const button = $("#accountButton");
  button.classList.toggle("authenticated", state.auth.authenticated);
  button.textContent = state.auth.authenticated ? String(state.auth.user || "A").slice(0, 2).toUpperCase() : "Sign in";
  button.title = state.auth.authenticated ? `Signed in as ${state.auth.user}` : "Sign in for protected operations";
}

function setView(name) {
  $$(".view").forEach(view => view.classList.toggle("active", view.id === `view-${name}`));
  $$(".nav-item[data-view]").forEach(item => item.classList.toggle("active", item.dataset.view === name));
  $("#pageEyebrow").textContent = pageMeta[name][0];
  $("#pageTitle").textContent = pageMeta[name][1];
  $("#sidebar").classList.remove("open");
  history.replaceState(null, "", `#${name}`);
}

function formatPorts(ports) {
  if (!ports?.length) return "—";
  return ports.slice(0, 3).map(port => port.PublicPort ? `${port.PublicPort}:${port.PrivatePort}` : `${port.PrivatePort}/${port.Type || "tcp"}`).join(", ");
}

function stateBadge(value) {
  const normalized = ["running", "partial"].includes(value) ? value : "stopped";
  return `<span class="state-badge ${normalized}">${escapeHtml(normalized)}</span>`;
}

function serviceLogo(key) {
  const initial = String(key || "?").charAt(0).toUpperCase();
  return `<span class="service-logo"><img src="/api/icons/${encodeURIComponent(key)}" alt=""><b>${escapeHtml(initial)}</b></span>`;
}

function stackActions(stack, compact = false) {
  if (stack.managed === false) {
    return `<span class="service-count" title="RogueForge protects its own Compose project from in-app lifecycle operations">Self-managed externally</span>`;
  }
  if (compact) {
    return `<button class="small-button accent" data-edit-stack="${attr(stack.name)}">Compose</button><button class="small-button" data-stack-action="restart" data-stack="${attr(stack.name)}">Restart</button>`;
  }
  return `
    <button class="primary-action" data-stack-action="start" data-stack="${attr(stack.name)}">Start</button>
    <button data-stack-action="stop" data-stack="${attr(stack.name)}">Stop</button>
    <button data-stack-action="restart" data-stack="${attr(stack.name)}">Restart</button>
    <button data-stack-action="pull" data-stack="${attr(stack.name)}">Pull</button>
    <button data-stack-action="recreate" data-stack="${attr(stack.name)}">Recreate</button>
    <button data-edit-stack="${attr(stack.name)}">Edit</button>`;
}

function renderOverview() {
  const running = state.containers.filter(item => item.state === "running").length;
  $("#stackCount").textContent = state.stacks.length;
  $("#containerCount").textContent = state.containers.length;
  $("#runningCount").textContent = running;
  $("#attentionCount").textContent = state.containers.length - running;
  $("#stackCaption").textContent = `${state.stacks.filter(item => item.state === "running").length} fully active`;
  $("#containerCaption").textContent = `Across ${state.status.engine}`;
  const rows = state.stacks.slice(0, 5).map(stack => `
    <div class="stack-row">
      <div class="stack-identity">${serviceLogo(stack.name)}<div><strong>${escapeHtml(stack.name)}</strong><small>${escapeHtml(stack.composeFile)}</small></div></div>
      ${stateBadge(stack.state)}
      <span class="service-count">${stack.running}/${stack.services} running</span>
      <div class="row-actions">${stackActions(stack, true)}</div>
    </div>`).join("");
  $("#overviewStacks").innerHTML = rows || '<div class="empty-state">No Compose stacks found in the configured directory.</div>';
}

function renderStacks() {
  const query = $("#stackSearch").value.trim().toLowerCase();
  const stacks = state.stacks.filter(stack => stack.name.toLowerCase().includes(query) || stack.composeFile.toLowerCase().includes(query));
  $("#stackGrid").innerHTML = stacks.map(stack => {
    const progress = stack.services ? Math.round(stack.running / stack.services * 100) : 0;
    return `<article class="stack-card">
      <div class="stack-card-top">
        <header><div class="stack-title">${serviceLogo(stack.name)}<div><h3>${escapeHtml(stack.name)}</h3><div class="file">${escapeHtml(stack.composeFile)}</div></div></div>${stateBadge(stack.state)}</header>
        <div class="stack-health"><div class="health-track"><i style="width:${progress}%"></i></div><strong>${progress}%</strong></div>
        <div class="stack-meta"><span>${stack.services} services</span><span>${stack.hasEnv ? ".env linked" : "No .env"}</span><span>${stack.managed === false ? "protected self stack" : escapeHtml(stack.engineHint)}</span></div>
      </div>
      <div class="stack-card-actions">${stackActions(stack)}</div>
    </article>`;
  }).join("") || '<div class="empty-state">No stacks match this filter.</div>';
}

function renderContainers() {
  const query = $("#containerSearch").value.trim().toLowerCase();
  const containers = state.containers.filter(item => [item.name, item.image, item.state].some(value => String(value).toLowerCase().includes(query)));
  $("#containerGrid").innerHTML = `<div class="container-head"><span>Container</span><span>Image</span><span>State</span><span>Ports</span><span></span></div>` + containers.map(container => `
    <div class="container-row">
      <div class="container-name">${serviceLogo(container.name)}<div><strong>${escapeHtml(container.name)}</strong><small>${escapeHtml(container.id)}</small></div></div>
      <span class="image-name" title="${attr(container.image)}">${escapeHtml(container.image)}</span>
      ${stateBadge(container.state)}
      <span class="port-list">${escapeHtml(formatPorts(container.ports))}</span>
      <div class="container-actions"><button class="small-button" data-container-action="restart" data-container="${container.id}">Restart</button><button class="small-button accent" data-logs="${container.id}" data-name="${attr(container.name)}">Logs</button></div>
    </div>`).join("") || '<div class="empty-state">No containers match this filter.</div>';
}

function renderStatus() {
  const engine = state.status.engine;
  $("#engineName").textContent = `${engine} connected`;
  $("#engineDetail").textContent = state.status.socket;
  $("#engineRuntime").textContent = engine;
  $("#engineInitial").textContent = engine.charAt(0).toUpperCase();
  $("#engineVersion").textContent = state.status.version;
  $("#apiVersion").textContent = state.status.apiVersion;
  $("#socketPath").textContent = state.status.socket;
  $("#engineContext").textContent = state.status.context || "default";
  $("#stacksPath").textContent = state.status.stacksDir;
  $("#publicUrl").textContent = state.status.publicUrl || "Not configured";
  $("#appVersion").textContent = state.status.appVersion ? `v${state.status.appVersion}` : "—";
  $("#stackNavCount").textContent = state.stacks.length;
  $("#containerNavCount").textContent = state.containers.length;
}

function renderAll() { renderStatus(); renderOverview(); renderStacks(); renderContainers(); }

async function load({ quiet = false } = {}) {
  if (state.loading) return;
  state.loading = true;
  $("#refreshButton").classList.add("spinning");
  try {
    [state.status, state.stacks, state.containers, state.auth] = await Promise.all([api("/api/status"), api("/api/stacks"), api("/api/containers"), api("/api/auth/session")]);
    renderAll();
    renderAuth();
    if (!quiet) toast("Infrastructure refreshed");
  } catch (error) {
    $("#engineName").textContent = "Connection error";
    $("#engineDetail").textContent = error.message;
    toast(error.message, "error");
  } finally {
    state.loading = false;
    $("#refreshButton").classList.remove("spinning");
  }
}

function confirmAction(title, message, button = "Continue") {
  $("#confirmTitle").textContent = title;
  $("#confirmMessage").textContent = message;
  $("#confirmButton").textContent = button;
  const dialog = $("#confirmDialog");
  dialog.showModal();
  return new Promise(resolve => dialog.addEventListener("close", () => resolve(dialog.returnValue === "confirm"), { once: true }));
}

async function stackAction(name, action) {
  if (!ensureAuthenticated()) return;
  const prompts = {
    stop: "Stops the services without removing the Compose project.",
    restart: "Restarts the services without taking the Compose project down.",
    recreate: "Recreates the project containers with the current Compose definition."
  };
  if (prompts[action] && !await confirmAction(`${action[0].toUpperCase() + action.slice(1)} ${name}?`, prompts[action], action[0].toUpperCase() + action.slice(1))) return;
  try {
    toast(`${action[0].toUpperCase() + action.slice(1)} started for ${name}`);
    const result = await api(`/api/stacks/${encodeURIComponent(name)}/${action}`, protectedOptions({ method: "POST" }));
    if (result.output) console.info(result.output);
    toast(`${name}: ${action} completed`);
    await load({ quiet: true });
  } catch (error) { toast(error.message, "error"); }
}

async function containerAction(id, action) {
  if (!ensureAuthenticated()) return;
  if (!await confirmAction(`${action[0].toUpperCase() + action.slice(1)} container?`, "The selected container may be briefly unavailable.", action[0].toUpperCase() + action.slice(1))) return;
  try { await api(`/api/containers/${id}/${action}`, protectedOptions({ method: "POST" })); toast(`Container ${action} completed`); setTimeout(() => load({ quiet: true }), 700); }
  catch (error) { toast(error.message, "error"); }
}

async function editStack(name) {
  if (!ensureAuthenticated()) return;
  try {
    const data = await api(`/api/stacks/${encodeURIComponent(name)}/compose`);
    state.currentStack = name;
    $("#editorTitle").textContent = name;
    $("#editorFile").textContent = data.name;
    $("#composeText").value = data.content;
    $("#editorDialog").showModal();
  } catch (error) { toast(error.message, "error"); }
}

async function saveCompose() {
  if (!ensureAuthenticated()) return;
  const button = $("#saveCompose");
  button.disabled = true;
  button.textContent = "Validating…";
  try {
    await api(`/api/stacks/${encodeURIComponent(state.currentStack)}/compose`, protectedOptions({ method: "PUT", body: JSON.stringify({ content: $("#composeText").value }) }));
    $("#editorDialog").close();
    toast("Compose validated, backed up, and saved");
    await load({ quiet: true });
  } catch (error) { toast(error.message, "error"); }
  finally { button.disabled = false; button.textContent = "Validate & save"; }
}

async function showLogs(id, name) {
  if (!ensureAuthenticated()) return;
  $("#logsTitle").textContent = name;
  $("#logText").textContent = "Loading logs…";
  $("#logsDialog").showModal();
  try { $("#logText").textContent = (await api(`/api/containers/${id}/logs`)).logs || "No log output."; }
  catch (error) { $("#logText").textContent = error.message; }
}

async function login(event) {
  event.preventDefault();
  const button = $("#loginButton");
  button.disabled = true;
  $("#loginError").textContent = "";
  try {
    const result = await api("/api/auth/login", { method: "POST", body: JSON.stringify({ username: $("#loginUsername").value, password: $("#loginPassword").value }) });
    state.auth = { configured: true, authenticated: true, user: result.user, csrf: result.csrf };
    $("#loginPassword").value = "";
    $("#loginDialog").close();
    renderAuth();
    await load({ quiet: true });
    toast(`Signed in as ${result.user}`);
  } catch (error) { $("#loginError").textContent = error.message; }
  finally { button.disabled = false; }
}

async function accountAction() {
  if (!state.auth.authenticated) { ensureAuthenticated(); return; }
  if (!await confirmAction("Sign out?", `End the administrator session for ${state.auth.user}?`, "Sign out")) return;
  try {
    await api("/api/auth/logout", protectedOptions({ method: "POST" }));
    state.auth = { configured: true, authenticated: false, user: null, csrf: null };
    renderAuth();
    await load({ quiet: true });
    toast("Signed out");
  } catch (error) { toast(error.message, "error"); }
}

document.addEventListener("click", event => {
  const nav = event.target.closest("[data-view]"); if (nav && !nav.classList.contains("disabled")) setView(nav.dataset.view);
  const go = event.target.closest("[data-go]"); if (go) setView(go.dataset.go);
  const stack = event.target.closest("[data-stack-action]"); if (stack) stackAction(stack.dataset.stack, stack.dataset.stackAction);
  const container = event.target.closest("[data-container-action]"); if (container) containerAction(container.dataset.container, container.dataset.containerAction);
  const editor = event.target.closest("[data-edit-stack]"); if (editor) editStack(editor.dataset.editStack);
  const logs = event.target.closest("[data-logs]"); if (logs) showLogs(logs.dataset.logs, logs.dataset.name);
});
document.addEventListener("error", event => {
  if (event.target.matches?.(".service-logo img")) event.target.closest(".service-logo").classList.add("fallback");
}, true);
$("#menuButton").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
$("#refreshButton").addEventListener("click", () => load());
$("#saveCompose").addEventListener("click", saveCompose);
$("#loginForm").addEventListener("submit", login);
$("#accountButton").addEventListener("click", accountAction);
$("#closeLogin").addEventListener("click", () => $("#loginDialog").close());
$("#cancelLogin").addEventListener("click", () => $("#loginDialog").close());
$("#stackSearch").addEventListener("input", renderStacks);
$("#containerSearch").addEventListener("input", renderContainers);
setView(pageMeta[location.hash.slice(1)] ? location.hash.slice(1) : "overview");
load({ quiet: true });
setInterval(() => load({ quiet: true }), 15000);
