/* Rogue theme kit 1.1, shared by RogueDashboard, RogueForge and RogueMediaValidator.
   Keep the three copies identical.

   - Preference: "default" (Rogue navy base, the starting theme), "light", "dark" or "system"
     (follows the device's light/dark setting), saved per browser.
   - Load it in <head> without defer: it sets html[data-theme] to the resolved "default", "light"
     or "dark" (and html[data-theme-pref]) before first paint.
   - Defines the chrome palette (--rogue-chrome*) for top bars and sidebars: navy in Default and
     Light, near-black in Dark. The accent is warm clay in every theme.
   - Any element with [data-rogue-theme-menu] becomes the top-bar theme button and menu.
   - Any button with [data-rogue-theme-choice="default|light|dark|system"] picks that theme and shows
     .active / aria-checked for the current choice.
   - Fires "rogue-theme-change" on document with detail {pref, resolved}.
   - window.RogueTheme: {pref(), resolved(), set(pref), setDefault(pref)}. setDefault() changes
     the fallback used when this browser has never picked a theme. */
(() => {
  "use strict";
  const KEY = "rogue-theme";
  const LEGACY_KEYS = ["rogueforge-theme"];
  const PREFS = ["default", "light", "dark", "system"];
  const LABELS = { default: "Default", light: "Light", dark: "Dark", system: "System" };
  const CHROME = { default: "#0f1a2e", light: "#0f1a2e", dark: "#181715" };
  const ICONS = {
    default: '<path d="M12 3.5c3.6 4.1 6 7.3 6 10.4a6 6 0 0 1-12 0c0-3.1 2.4-6.3 6-10.4Z"/>',
    system: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    light: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>',
    dark: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  };
  const icon = (name, size = 16) =>
    `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${ICONS[name]}</svg>`;
  const media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: light)") : null;
  const read = key => { try { return localStorage.getItem(key); } catch (error) { return null; } };
  const write = (key, value) => { try { localStorage.setItem(key, value); } catch (error) { /* private mode */ } };
  let fallback = "default";

  function stored() {
    const value = read(KEY);
    if (PREFS.includes(value)) return value;
    const legacy = LEGACY_KEYS.map(read).find(item => PREFS.includes(item));
    if (legacy) write(KEY, legacy);
    return legacy || null;
  }
  const pref = () => stored() || fallback;
  const resolved = (value = pref()) => (value === "system" ? (media && media.matches ? "light" : "dark") : value);

  function paint() {
    const current = pref();
    document.querySelectorAll("[data-rogue-theme-choice]").forEach(button => {
      const on = button.dataset.rogueThemeChoice === current;
      button.classList.toggle("active", on);
      button.setAttribute("aria-checked", String(on));
    });
    document.querySelectorAll(".rogue-theme-trigger").forEach(button => {
      button.innerHTML = icon(current, 17);
      button.title = `Theme: ${LABELS[current]}`;
      button.setAttribute("aria-label", `Theme: ${LABELS[current]}`);
    });
  }

  function apply() {
    const root = document.documentElement;
    const current = pref();
    const mode = resolved(current);
    const changed = root.dataset.theme !== mode || root.dataset.themePref !== current;
    root.dataset.theme = mode;
    root.dataset.themePref = current;
    document.querySelectorAll('meta[name="theme-color"]').forEach(meta => { meta.removeAttribute("media"); meta.content = CHROME[mode]; });
    paint();
    if (changed) document.dispatchEvent(new CustomEvent("rogue-theme-change", { detail: { pref: current, resolved: mode } }));
  }

  function set(value) {
    write(KEY, PREFS.includes(value) ? value : "default");
    apply();
  }

  function setDefault(value) {
    fallback = PREFS.includes(value) ? value : "default";
    apply();
  }

  function closeAll(except) {
    document.querySelectorAll(".rogue-theme").forEach(host => {
      if (host === except) return;
      const menu = host.querySelector(".rogue-theme-menu");
      if (menu && !menu.hidden) {
        menu.hidden = true;
        host.querySelector(".rogue-theme-trigger")?.setAttribute("aria-expanded", "false");
      }
    });
  }

  function mount(host) {
    if (host.dataset.rogueThemeMounted) return;
    host.dataset.rogueThemeMounted = "1";
    host.classList.add("rogue-theme");
    host.innerHTML = `<button type="button" class="rogue-theme-trigger" aria-haspopup="menu" aria-expanded="false"></button>`
      + `<div class="rogue-theme-menu" role="menu" aria-label="Theme" hidden><p class="rogue-theme-heading">Theme</p>`
      + PREFS.map(value => `<button type="button" role="menuitemradio" data-rogue-theme-choice="${value}">${icon(value)}<span>${LABELS[value]}</span><i>${icon("check", 15)}</i></button>`).join("")
      + `</div>`;
    const trigger = host.querySelector(".rogue-theme-trigger");
    const menu = host.querySelector(".rogue-theme-menu");
    trigger.addEventListener("click", event => {
      event.stopPropagation();
      const open = menu.hidden;
      closeAll(host);
      menu.hidden = !open;
      trigger.setAttribute("aria-expanded", String(open));
      if (open) (menu.querySelector(".active") || menu.querySelector("button")).focus();
    });
    menu.addEventListener("keydown", event => {
      const items = [...menu.querySelectorAll("button")];
      const index = items.indexOf(document.activeElement);
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        items[(index + (event.key === "ArrowDown" ? 1 : items.length - 1)) % items.length].focus();
      } else if (event.key === "Escape" || event.key === "Tab") {
        closeAll();
        if (event.key === "Escape") trigger.focus();
      }
    });
    paint();
  }

  const scan = () => document.querySelectorAll("[data-rogue-theme-menu]:not([data-rogue-theme-mounted])").forEach(mount);

  document.addEventListener("click", event => {
    const choice = event.target.closest && event.target.closest("[data-rogue-theme-choice]");
    if (choice) {
      set(choice.dataset.rogueThemeChoice);
      const host = choice.closest(".rogue-theme");
      if (host) { closeAll(); host.querySelector(".rogue-theme-trigger")?.focus(); }
      return;
    }
    if (!(event.target.closest && event.target.closest(".rogue-theme"))) closeAll();
  });
  document.addEventListener("keydown", event => { if (event.key === "Escape") closeAll(); });
  if (media) {
    const follow = () => { if (pref() === "system") apply(); };
    if (media.addEventListener) media.addEventListener("change", follow); else if (media.addListener) media.addListener(follow);
  }
  window.addEventListener("storage", event => { if (event.key === KEY) apply(); });

  const style = document.createElement("style");
  style.id = "rogue-theme-kit";
  style.textContent = [
    ":root{--rogue-chrome:#181715;--rogue-chrome-2:#232220;--rogue-chrome-3:#2c2c2a;--rogue-chrome-field:#1b1a19;--rogue-chrome-line:rgba(222,220,209,.1);--rogue-chrome-line-strong:rgba(222,220,209,.2);--rogue-chrome-text:#faf9f5;--rogue-chrome-text-2:#dedcd3;--rogue-chrome-muted:#b0aea5;--rogue-chrome-faint:#8a8880;--rogue-chrome-hover:rgba(222,220,209,.07);--rogue-chrome-active:rgba(222,220,209,.11)}",
    ":root[data-theme=default],:root[data-theme=light]{--rogue-chrome:#0f1a2e;--rogue-chrome-2:#172540;--rogue-chrome-3:#1e2f50;--rogue-chrome-field:#0c1526;--rogue-chrome-line:rgba(196,214,255,.11);--rogue-chrome-line-strong:rgba(196,214,255,.22);--rogue-chrome-text:#f4f4f5;--rogue-chrome-text-2:#dfe3ec;--rogue-chrome-muted:#a9b1c3;--rogue-chrome-faint:#7d879b;--rogue-chrome-hover:rgba(196,214,255,.07);--rogue-chrome-active:rgba(196,214,255,.12)}",
    ".rogue-theme{position:relative;display:inline-flex;flex:none}",
    ".rogue-theme-trigger{width:38px;height:38px;display:grid;place-items:center;padding:0;border:1px solid var(--rogue-chrome-line-strong);border-radius:10px;background:var(--rogue-chrome-hover);color:var(--rogue-chrome-text-2);cursor:pointer;transition:background .12s ease,border-color .12s ease,color .12s ease}",
    ".rogue-theme-trigger:hover,.rogue-theme-trigger[aria-expanded=true]{background:var(--rogue-chrome-active);color:var(--rogue-chrome-text)}",
    ".rogue-theme-trigger:focus-visible,.rogue-theme-menu button:focus-visible{outline:2px solid #d97757;outline-offset:2px}",
    ".rogue-theme-menu{position:absolute;right:0;top:calc(100% + 8px);z-index:1000;min-width:208px;padding:6px;border:1px solid var(--rogue-chrome-line-strong);border-radius:12px;background:var(--rogue-chrome-2);color:var(--rogue-chrome-text);box-shadow:0 18px 44px -14px rgba(0,0,0,.6);color-scheme:dark}",
    ".rogue-theme-menu[hidden]{display:none}",
    ".rogue-theme-heading{margin:0;padding:8px 10px 6px;color:var(--rogue-chrome-faint);font:700 10.5px/1.2 Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;letter-spacing:.09em;text-transform:uppercase}",
    ".rogue-theme-menu button{width:100%;height:36px;display:flex;align-items:center;gap:11px;padding:0 10px;border:0;border-radius:8px;background:transparent;color:var(--rogue-chrome-text-2);font:550 13px/1 Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;text-align:left;cursor:pointer}",
    ".rogue-theme-menu button svg{flex:none;color:var(--rogue-chrome-muted)}",
    ".rogue-theme-menu button:hover{background:var(--rogue-chrome-hover);color:var(--rogue-chrome-text)}",
    ".rogue-theme-menu button.active{background:var(--rogue-chrome-active);color:var(--rogue-chrome-text);font-weight:650}",
    ".rogue-theme-menu button.active svg{color:var(--rogue-chrome-text)}",
    ".rogue-theme-menu i{margin-left:auto;display:grid;color:#d97757;visibility:hidden}",
    ".rogue-theme-menu button.active i{visibility:visible}",
    ".rogue-theme-menu button.active i svg{color:#d97757}",
    ".rogue-theme-menu button[data-rogue-theme-choice=system]{margin-top:4px;position:relative}",
    ".rogue-theme-menu button[data-rogue-theme-choice=system]::before{content:'';position:absolute;left:4px;right:4px;top:-3px;border-top:1px solid var(--rogue-chrome-line)}",
    "@media (prefers-reduced-motion:reduce){.rogue-theme-trigger{transition:none}}",
  ].join("");
  (document.head || document.documentElement).appendChild(style);

  window.RogueTheme = { pref, resolved: () => resolved(), set, setDefault };
  apply();
  scan();
  new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true });
})();
