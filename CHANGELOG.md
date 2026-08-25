# Changelog

## 0.8.2 — Single-runtime consolidation and release cleanup

- Consolidated RogueForge backend functionality into the single canonical `rogueforge.py` runtime.
- Removed historical `rogueforge_v*.py` wrappers and the `rogueforge_ext.py`, `rogueforge_live.py`, and `rogueforge_discovery.py` extension layers.
- Preserved flexible recursive Compose discovery, Podman/Docker compatibility, stack/service lifecycle operations, Compose and `.env` editing, update checks, bulk runtime controls, resource statistics, live logs, terminal/exec, authentication, CSRF protection, and RogueForge self-protection in the consolidated runtime.
- Kept Podman Compose 1.x compatibility: no unsupported `--env-file` global argument and no unsupported `config` subcommand.
- Added `update.sh` as the supported update path and retired the old `upgrade.sh` workflow.
- Updated Containerfile to copy and launch only `rogueforge.py` plus the account helper and static web assets.
- Added CI syntax validation and an explicit guard that rejects reintroduction of legacy runtime wrapper/extension files.
- Updated Compose, installer, environment example and GHCR defaults to `0.8.2`.
- Cleaned RogueForge branding to the approved Base, Dark, and Light SVG assets only.
- Updated the web UI branding switcher to use those three assets.
- Updated README, roadmap and release documentation for the consolidated architecture.

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
