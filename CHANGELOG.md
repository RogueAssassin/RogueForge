# Changelog

## 0.8.5 — Podman runtime reliability and UI consistency

- Fixed Compose-managed container Update on Podman Compose 1.5.0 by pulling the actual container image with Podman and using Compose only to recreate the target service.
- Hardened CPU/RAM statistics parsing for Podman JSON arrays, line-delimited JSON, alternate field names, container IDs and container names.
- Made active runtime Compose labels authoritative during stack discovery and suppresses duplicate filesystem candidates for the same active project.
- Moved Compose-editor and `.env` backups outside the stack tree under `/tmp/rogueforge/` alongside update backups.
- Improved Nginx Proxy Manager and Cloudflared icon selection by preferring active container image/service identity over generic project names.
- Standardized icon centering and safe-area sizing across Overview, Stacks and Runtime.
- Reworked Runtime actions into aligned primary and secondary action grids instead of free-wrapping buttons.
- Added a dedicated testing release channel (`:testing` and branch tags) so fixes can be validated on FEILSBEASTSERVER without touching production aliases.
- Added pre-publish container-build validation and regression coverage for Podman updates, stats, discovery, backups, icon identity and testing-channel behavior.
- Advanced testing metadata to v0.8.5; production aliases remain unchanged until the tested branch is promoted to `main`.

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
