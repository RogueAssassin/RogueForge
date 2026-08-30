# Changelog

## 0.9.0 — Runtime resources, operations quality and production-readiness milestone

- Applied the cleaner 0.9 production-candidate visual system directly to the app: icon-led metric cards, centered Quick Actions, tighter sidebar/topbar spacing, cleaner stack rows, aligned System Information, matching resource cards and a lightweight application footer.
- Preserved the existing RogueForge branding/icon assets unchanged while modernizing the surrounding UI.

- Added first-class read-only Images, Volumes and Networks inventory pages that load on demand so resource discovery does not slow Overview/Stacks/Runtime.
- Refined Overview summary cards, System Information rows and Quick Actions into centered, consistent layouts based on the cleaner 0.9 visual baseline.

- Hardened canonical frontend rendering against optional/removed DOM nodes after the v0.8 asset consolidation, fixing `Cannot set properties of null (setting 'textContent')` failures on the current testing UI.

- Consolidated the remaining version-named v0.8 frontend assets into canonical `static/app.js` and `static/styles.css`, removed the compatibility files from runtime loading, and added CI/test guards against future version-named frontend assets.
- Removed obsolete 0.8.2 release notes and unused 0.4.x banner assets from the active repository tree.

- Stopped the updater from overwriting its own executable while Bash is still reading it; the downloaded updater is now installed only after a verified healthy deployment, preventing mixed-script syntax failures during channel upgrades.
- Added CI shell syntax validation for `update.sh` and `install.sh` plus a regression test that enforces safe updater replacement ordering.

- Fixed release tests and installer metadata for the 0.9.0 testing rollover so CI derives version expectations from the canonical `VERSION` file instead of a stale hard-coded 0.8.8 value.

- Added watchdog-backed operation timeouts that also terminate silent/hung Compose processes, plus configurable terminate-to-kill grace handling.
- Added explicit `timed_out`, cancellation and failure-reason operation states with persisted step/progress metadata for the Operations drawer.

- Consolidated the historical versioned runtime patch tools into one canonical `tools/prepare_runtime.py` pipeline and updated CI/tests to reject future version-named patch-tool sprawl.
- Rewrote stale installation and container-deployment documentation for the current `main`/`testing`, configurable-root and deterministic Podman lifecycle model.

- Refreshed the repository presentation to match the RogueDashboard family: product header, release/GHCR/build/runtime/engine/platform badges and clearer Rogue ecosystem cross-linking.
- Added a direct RogueDashboard download/repository link and clarified the split between RogueForge management and RogueDashboard visibility.
- Expanded the 0.9.0 roadmap around operation timeouts/recovery, persistent audit history, transactional configuration saves, coalesced refreshes, targeted cache invalidation, batched stats, endpoint timing diagnostics, security hardening and compatibility testing.
- Keeps the validated 0.8.7 dashboard snapshot, Podman lifecycle, updater verification, configurable roots, inventory caching and non-blocking runtime refresh work as the baseline.
- Keeps `main` production-only; 0.9.0 remains on the permanent `testing` channel until regression-tested and promoted.

## 0.8.7 — Fast dashboard snapshots and non-blocking refresh

- Added a unified `/api/dashboard` endpoint so the initial web UI receives status, stacks, containers and authentication/session state in one request instead of four separate requests.
- Added short-lived browser session snapshot hydration so the last known dashboard can render immediately while fresh runtime state is requested in the background.
- Kept CPU/RAM statistics on their own asynchronous refresh path so expensive stats collection does not block initial page rendering or normal navigation.
- Increased visible runtime refresh cadence to 10 seconds while avoiding refreshes in hidden browser tabs and forcing a quick refresh when a stale tab becomes visible again.
- Reused the shared short-lived Podman inventory cache introduced in 0.8.6 so dashboard snapshot generation does not multiply engine inventory calls.
- Established the permanent two-branch development model: `testing` for active development and `main` for production-only promotion.
- Testing images publish only as `testing` plus immutable SHA tags; testing never updates `latest`, semantic version aliases, or production release tags.
- Updated the updater so `./update.sh testing` resolves the permanent `testing` branch instead of a version-specific testing branch.
- Retains the deterministic media-server lifecycle contract: Start=`up -d`, Stop=`down`, Restart/Recreate=`down` then `up -d`, Stack Update=`pull` then `down` then `up -d`.

## 0.8.6 — Verified Podman replacement, fast inventory and configurable stack roots

- Reworked Compose-managed Podman updates so RogueForge pulls the image, compares immutable image IDs, preserves the old container under a temporary name, recreates the service from the authoritative Compose definition, verifies the new running image ID, and removes the preserved container only after successful verification.
- Added recovery logic that attempts to restore and restart the preserved previous container if recreation or image verification fails.
- Added `ROGUEFORGE_MEDIA_ROOT`, `ROGUEFORGE_COMPOSE_ROOT`, and `ROGUEFORGE_ENV_ROOT` so administrators can separate the mounted host root from Compose discovery and `.env` locations.
- Kept `ROGUEFORGE_STACKS_DIR` as a compatibility alias synchronized to `ROGUEFORGE_COMPOSE_ROOT` by the updater.
- Added mirrored `.env` resolution: the relative stack path beneath `COMPOSE_ROOT` is resolved beneath `ENV_ROOT`, while the common case keeps Compose and `.env` files together.
- Added API diagnostics/status reporting for media, Compose and environment roots.
- Eliminated the container inventory N+1 query pattern and added a shared short-lived `ROGUEFORGE_INVENTORY_CACHE` (2 seconds by default) so Overview, Stacks and Runtime can reuse the same Podman snapshot during page load.
- Stopped forcing a full Compose discovery rebuild on every `/api/stacks` request; normal UI requests now honor the discovery cache while diagnostics remains the explicit refresh path.
- Aligned Podman stack lifecycle operations with the proven media-server `compose_for` contract: Start uses `up -d`, Stop uses `down`, Restart/Recreate use `down` then `up -d`, and Stack Update uses `pull`, `down`, then `up -d`.
- Added proper HTTP `HEAD` support and treats client disconnects/BrokenPipe events as normal disconnects rather than cascading them into misleading HTTP 500 responses.
- Updated the testing channel to `v0.8.6-testing` and retained isolated `testing`, branch and SHA GHCR tags without touching production aliases.
- Retained the 0.8.5 CPU/RAM parsing, active-label discovery precedence, external backups, icon identity and Runtime layout fixes.
- Added regression checks for configurable roots, verified Podman replacement, shared inventory caching, media-server lifecycle behavior, HTTP hardening and testing-channel packaging.

## 0.8.5 — Podman runtime reliability and UI consistency

- Fixed Compose-managed container Update on Podman Compose 1.5.0 by pulling the actual container image with Podman and using Compose only to recreate the target service.
- Hardened CPU/RAM statistics parsing for Podman JSON arrays, line-delimited JSON, alternate field names, container IDs and container names.
- Made active runtime Compose labels authoritative during stack discovery and suppresses duplicate filesystem candidates for the same active project.
- Moved Compose-editor and `.env` backups outside the stack tree under `/tmp/rogueforge/` alongside update backups.
- Improved Nginx Proxy Manager and Cloudflared icon selection by preferring active container image/service identity over generic project names.
- Standardized icon centering and safe-area sizing across Overview, Stacks and Runtime.
- Reworked Runtime actions into aligned primary and secondary action grids instead of free-wrapping buttons.
- Added a dedicated testing release channel (`:testing` and branch tags) so fixes can be validated without touching production aliases.
- Added pre-publish container-build validation and regression coverage for Podman updates, stats, discovery, backups, icon identity and testing-channel behavior.

## 0.8.4 — Operations visibility, health filtering and release correctness

- Added stack health filters for All, Healthy, Partial and Stopped workloads directly above the stack list.
- Added stronger stack-edge and service-row fault highlighting so partial/stopped workloads are easier to identify at a glance.
- Expanded the Operations drawer with running/success/failed filtering.
- Added JSON export of recent Operations history for troubleshooting and support.
- Increased retained browser operation history and captured output limits while keeping completed-history cleanup.
- Consolidated the v0.8.3 operations/icon layer into canonical non-versioned `static/operations.js` and `static/operations.css` assets; removed the unused `v083` frontend files.
- Retained layered Dashboard Icons resolution and explicit Nginx Proxy Manager / Cloudflared aliases.
- Fixed a release-workflow gap where validation stamped the runtime version but the publish job built from the unstamped checkout.
- Hardened CI and advanced deployment defaults to v0.8.4.

## 0.8.3 — Operations quality, icon reliability and release workflow

- Moved updater deployment backups out of `/opt/media-server` and into `/tmp/rogueforge-update-backups` so backup Compose snapshots are not discovered as dashboard stacks.
- Added automatic migration of legacy `data/update-backups` contents into the external temporary backup area.
- Hardened recursive stack discovery to ignore update backup directories.
- Added an Operations activity drawer with status, timestamps, duration and captured output.
- Added layered Dashboard Icons resolution and explicit Nginx Proxy Manager / Cloudflared aliases.
- Added `VERSION` metadata and GHCR `latest`, semantic, v-prefixed, compact and SHA tags.

## 0.8.2 — Single-runtime consolidation and release cleanup

- Consolidated RogueForge backend functionality into the single canonical `rogueforge.py` runtime.
- Removed historical `rogueforge_v*.py` wrappers and backend extension layers.
- Preserved flexible recursive Compose discovery, Podman/Docker compatibility, lifecycle operations, editing, statistics, logs, terminal, authentication and self-protection.
- Added `update.sh` and retired `upgrade.sh`.
- Updated Containerfile and CI for the single runtime.

## 0.8.1 — UI and centralized icon integration

- Refined the stack-first dark operations interface.
- Added Dashboard Icons CDN resolution with local fallbacks.
- Added RogueForge branding variants and browser/sidebar branding controls.
- Fixed installer validation for Podman Compose implementations without a `config` subcommand.

## 0.8.0 — Stack-first operations

- Made Stacks the primary Compose management surface and repositioned Containers as the advanced Runtime view.
- Added expandable stack services with individual lifecycle, Update, Logs, and Terminal controls.
- Added Stack Update and stack `.env` editing with backup and validation.
- Added runtime-aware Compose validation for Podman Compose 1.x.

## 0.7.1 — Flexible Compose discovery

- Replaced the old project-name-equals-directory assumption with a discovery registry.
- Added Compose config-file and working-directory label resolution.
- Added recursive Compose scanning with configurable depth and caching.
- Added authenticated discovery diagnostics.

## 0.7.0 — Live operations

- Added authenticated live container log streaming over Server-Sent Events.
- Added searchable/pauseable/downloadable live logs.
- Added authenticated container terminal sessions with Bash-to-`sh` fallback and cleanup.

## 0.6.2 — Bulk runtime operations

- Added multi-select and bulk Start, Stop, Restart, Update, Recreate, and Remove operations.
- Added container sorting, resource usage, restart policy visibility, and aggregate action feedback.

## 0.6.1 — Update awareness

- Added container resource statistics, per-container update checks, and Update All.

## 0.6.0 — Container lifecycle management

- Added Compose-aware per-container lifecycle, Update, Recreate, Inspect, Logs, and Remove operations.
- Added standalone image pulling and self-container protection.

## 0.5.0 — Rootless Podman reliability

- Unified rootless Podman operations around the mounted host socket.
- Fixed deployment runtime detection, stack stop/restart behavior, and self-stack protection.
