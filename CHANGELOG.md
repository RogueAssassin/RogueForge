# Changelog

## 0.8.4 — Operations visibility, health filtering and release correctness

- Added stack health filters for All, Healthy, Partial and Stopped workloads directly above the stack list.
- Added stronger stack-edge and service-row fault highlighting so partial/stopped workloads are easier to identify at a glance.
- Expanded the Operations drawer with running/success/failed filtering.
- Added JSON export of recent Operations history for troubleshooting and support.
- Increased retained browser operation history and captured output limits while keeping completed-history cleanup.
- Consolidated the v0.8.3 operations/icon layer into canonical non-versioned `static/operations.js` and `static/operations.css` assets; removed the unused `v083` frontend files.
- Retained layered Dashboard Icons resolution and explicit Nginx Proxy Manager / Cloudflared aliases.
- Fixed a release-workflow gap where validation stamped the runtime version but the publish job built from the unstamped checkout. The publish job now stamps and verifies the exact `VERSION` before the multi-architecture image build.
- Hardened CI to reject reintroduction of the old v0.8.3 frontend assets and require the canonical operations assets.
- Advanced release metadata and deployment defaults to v0.8.4.

## 0.8.3 — Operations quality, icon reliability and release workflow

- Moved updater deployment backups out of `/opt/media-server` and into `/tmp/rogueforge-update-backups` (or `$TMPDIR/rogueforge-update-backups`) so backup Compose snapshots are not discovered as dashboard stacks.
- Added automatic migration of legacy `data/update-backups` contents into the external temporary backup area.
- Hardened recursive stack discovery in the packaged runtime to ignore `update-backups` and `rogueforge-update-backups` directory names.
- Added an Operations activity drawer that records stack/container mutation operations with running/success/failure status, timestamps, duration and captured output.
- Persisted recent Operations history in browser local storage with a clear-completed action.
- Reworked service icon handling to use layered Dashboard Icons resolution: jsDelivr → raw GitHub → RogueForge local endpoint → generic Docker icon.
- Added explicit icon aliases for Nginx Proxy Manager (`nginx-proxy-manager.svg`) and Cloudflared (`cloudflare.svg`) plus common alternate names/image references.
- Ensured the service initial remains visible if every icon source is unavailable, preventing blank stack/service identity tiles.
- Added `VERSION` release metadata and prepared v0.8.3 packaging while retaining the single `rogueforge.py` application runtime.
- Updated GHCR publishing to support `latest`, semantic (`0.8.3`), v-prefixed (`v0.8.3`), compact (`083`) and SHA tags.
- Updated the release workflow to create the matching immutable Git version tag when a new version is first published.
- Kept deployment tooling sourced from `main` so updater/Compose fixes remain available when installing a pinned runtime image.

## 0.8.2 — Single-runtime consolidation and release cleanup

- Consolidated RogueForge backend functionality into the single canonical `rogueforge.py` runtime.
- Removed historical `rogueforge_v*.py` wrappers and the `rogueforge_ext.py`, `rogueforge_live.py`, and `rogueforge_discovery.py` extension layers.
- Preserved flexible recursive Compose discovery, Podman/Docker compatibility, stack/service lifecycle operations, Compose and `.env` editing, update checks, bulk runtime controls, resource statistics, live logs, terminal/exec, authentication, CSRF protection, and RogueForge self-protection in the consolidated runtime.
- Added `update.sh` as the supported update path and retired the old `upgrade.sh` workflow.
- Updated Containerfile to copy and launch only `rogueforge.py` plus the account helper and static web assets.
- Added CI syntax validation and an explicit guard that rejects reintroduction of legacy runtime wrapper/extension files.

## 0.8.1 — UI and centralized icon integration

- Refined the stack-first dark operations interface.
- Added Dashboard Icons CDN resolution for general stack/service artwork with local fallbacks.
- Added RogueForge branding variants and browser/sidebar branding controls.
- Fixed installer validation for Podman Compose implementations without a `config` subcommand.

## 0.8.0 — Stack-first operations

- Made Stacks the primary Compose management surface and repositioned Containers as the advanced Runtime view.
- Added expandable stack services with individual lifecycle, Update, Logs, and Terminal controls.
- Added Stack Update (`pull` followed by `up -d --remove-orphans`).
- Added stack `.env` editing with backup and validation.
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
