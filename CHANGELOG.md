# Changelog

## 2.6.2

- Fixed: the Images page showed image creation time as a raw number (Podman reports a Unix timestamp); it now shows a date.
- Fixed: the sign-in and confirmation dialogs were much wider than their contents.
- Fixed: after signing in, the open page stayed on "authentication required" until refreshed.

## 2.6.1

- Fixed: on windows narrower than about 1240px the Runtime table hid its Ports and Actions columns off to the right. It now shows each container as a card there, and never scrolls sideways.

## 2.6.0

- **New interface.** One SVG icon set replaces the text-symbol icons; the sidebar is grouped (Workloads, Resources, Maintenance); each page names itself once; the Overview opens with a status banner; cards, buttons, chips, dialogs and hover states are restyled with a brighter accent gradient in all themes.
- Runtime actions are compact icon buttons (labels stay as tooltips and for screen readers), and the runtime table becomes stacked cards on phones.
- Fixed: the Runtime **Ports** column showed `undefined/tcp`; it now shows the published and container ports.
- No new dependencies or external requests.

## 2.5.0

- **Clean up from the Images and Volumes pages.** Unused images and volumes get a **Remove** button, **Remove dangling** and **Remove unused…** clean up in bulk, and a confirmation lists exactly what will go. Volumes hold data, so deleting one (or several) needs a typed confirmation.
- Safe by design: usage is re-checked on the server for every request, anything with a container (running or stopped) is skipped, and the engine runs without `--force`, so it refuses anything still referenced. New endpoints `POST /api/images/remove`, `POST /api/images/prune` and `POST /api/volumes/remove` (administrator only, CSRF protected). Image sizes now show in MB/GB with the reclaimable total.
- **Updates page improvements:** updates are sorted first; filter chips (All, Updates, Failed, Not checked) and a search box; relative times with the next scheduled check; an **Update** button for moving tags (the normal verified pull, recreate and rollback, then an automatic re-check) and **Edit Compose** for pinned version tags; a clearer summary when everything is current or some checks failed.
- Invalid request bodies now answer `400` instead of `500`.

## 2.4.2

Adds the built-in Updates page.

- Built-in **Updates** page: shows which containers have a newer image, with an alert count in the sidebar and a **Check now** button. Versioned tags are compared with the registry tag list (major/minor/patch); moving tags such as `latest` are compared by digest. Works with Docker and rootless Podman.
- Runs inside RogueForge with anonymous registry reads only: no extra container, no extra socket mount, nothing is pulled or changed. Background scan every 6 hours by default.
- New endpoints `GET /api/updates` and `POST /api/updates/check` (administrator only). New settings `ROGUEFORGE_UPDATES`, `ROGUEFORGE_UPDATE_INTERVAL`, `ROGUEFORGE_UPDATE_TIMEOUT`, `ROGUEFORGE_UPDATE_CONCURRENCY`; all are optional and default sensibly, so existing `.env` files keep working.
- Bundled Docker CLI updated to 29.10.0 (Dependabot).
- Documentation: Updates page screenshots (sample data), a badge reference in the README, an update-checker section in the install and security guides, and the new settings in `.env.example`.
- Version bumped to 2.4.2 (`VERSION`, `install.sh`, `rogueforge.py`, `compose.yaml`, `.env.example`).

## 2.4.1

Light theme readability update, aligned with RogueDashboard 2.4.1 and RogueMediaValidator 1.4.1.

- Softer Light theme: the near-white surfaces are replaced by a cool blue-grey that matches the navy (page #cfd8e4, cards #e6ebf2, tiles #d9e0ea) with navy text, stronger borders and darker secondary text and status colours. All dashboard text now meets WCAG AA contrast in Light.
- Theme menu heading is easier to read on the navy chrome.
- Tidier Activity drawer: finished operations fold their output (it was always expanded because of an `open=""` attribute), only running ones show the live step and output, long lines wrap instead of scrolling sideways, and a summary line shows how many are running and finished.
- Activity can be cleaned up: **Clear all** removes every finished operation and **Trim** keeps the last 5, 10 or 25. Running operations are never removed. Backed by `DELETE /api/operations?keep=N` (administrator only).
- History is now capped at 50 finished operations by default (was 120), set with `ROGUEFORGE_OPERATIONS_KEEP` (5-500); older ones are dropped automatically.
- CI now syntax-checks the front-end JavaScript.

## 2.4.0

Clean visual refresh and dependency update, aligned with RogueDashboard 2.4.0 and RogueMediaValidator 1.4.0.

- New look: a Rogue navy **Default** theme, a warm paper **Light** theme and a warm charcoal **Dark** theme, all with one clay accent, replacing the purple/cyan neon styling. All colours now come from one token set, so every screen supports every theme.
- New theme button at the top right with **Default**, **Light**, **Dark** and **System** (follows the device), saved per browser and applied before first paint. It is the same menu in RogueDashboard and RogueMediaValidator (shared `rogue-theme.js`, which replaces `theme-init.js`; a theme picked in 2.4 testing carries over). The sidebar and top bar stay navy in Default and Light and near-black in Dark. The theme buttons in Settings were removed; Settings keeps the icon variant choice.
- Overview tiles carry a soft tint of their status colour.
- Kept the original RogueForge icons.
- Fixed: on Podman, `update.sh` refused every update after the first ("Another update is already running") because the container's conmon process inherited the update lock. One-time fix on existing installs: remove `.update.lock` in the install folder, then update.
- Fixed: the stylesheet referenced a missing `rogueforge-base.svg`, which the server answered with the HTML index page.
- Fixed: the operations count badge showed as an empty dot when nothing was running.
- Bundled podman-compose 1.6.0 (checksum pinned) and Docker CLI 29.9.3.

## 2.3.0

- Promoted the testing line to production on top of the 2.0.1 hardening release.
- Service icons: RogueDashboard now shows its own dashboard-icons logo instead of the generic one, Pi-hole maps to `pi-hole`, PNG-only icons are tried after SVG, and RogueForge uses its bundled logo. Dropped the dead `/api/icons` and duplicate raw-GitHub fallbacks, and failed icon URLs are no longer re-requested on every re-render.
- Faster connects: container inventory now reads the engine API socket first (Docker and Podman alike) instead of spawning `podman --remote ps` per scan; set `ROGUEFORGE_INVENTORY_SOURCE=cli` to restore the old order. Each source falls back to the other.
- Fixed the inventory cache being stamped before the engine query ran, so a slow query expired it immediately and one dashboard build ran the query up to three times (about 4.4 s cold). Concurrent callers now share a single query.
- Added a background warmer (`ROGUEFORGE_DASHBOARD_WARM`, default 15 s, 0 disables) that keeps the dashboard snapshot inside the stale window, so the first visit after idle no longer waits for a cold scan.
- Moved the image to Debian trixie for the Podman 5.4 remote client. The previous 4.3 client made podman-compose skip `depends_on: condition: service_healthy` waits during in-app stack actions.
- Bumped the bundled Docker CLI to 29.9.0.

## 2.0.1

- Made `tini` PID 1 so `podman stop`/`docker stop` end RogueForge immediately and engine or Compose child processes are reaped.
- Bundled a static Docker CLI with the Compose v2 plugin so in-app stack actions work on Docker hosts; removed the unused Docker daemon from the image. The Podman remote client is unchanged.
- Replaced the bundled podman-compose 1.0.3 with 1.5.0. The old release failed every in-app action with `missing networks` on stacks whose services use network `aliases:` (RogueMediaValidator, RogueDashboard, RogueRoute GPX) and ignored `x-podman` and the `PODMAN_COMPOSE_*` settings RogueForge passes.
- Defined the health check in `compose.yaml` and added `no-new-privileges`, memory and PID ceilings, log rotation and a stop grace period.
- Added the optional `ROGUEFORGE_HOST_BIND`, `ROGUEFORGE_MEM_LIMIT` and `ROGUEFORGE_PIDS_LIMIT` settings; existing `.env` files keep working without them.
- Made `update.sh` pull before changing deployment files, take a lock, read the health port from `.env`, prune old backups and roll back the deployment files and image on failure.
- Fixed `install.sh` on Docker hosts where the shared network already exists.
- Added `.dockerignore`, Dependabot, least-privilege CI permissions, an image smoke test, build provenance and SBOM.

## 2.0.0 (testing)

- Established RogueForge API version 2 and persistent-state schema version 1.
- Added stable read-only `/api/v2/status` and `/api/v2/contract` endpoints.
- Added API/state contract metadata to the RogueDashboard integration payload.
- Declared backward compatibility from the validated 1.9.0 state baseline; no data migration is required for this testing candidate.
- Preserved the verified lifecycle, update preview, image verification, rollback, bounded logging, terminal and operation-history systems.
- Kept the default `.env` unchanged because 2.0.0 introduces no new runtime environment command.
- Kept 2.0.0 on the permanent `testing` branch pending live-host validation before main/latest promotion.

## 1.9.0 (testing)

- Established the final 1.x cleanup baseline before RogueForge 2.0.
- Removed no-op environment revision blocks and cleaned the repository for the major-version transition.

