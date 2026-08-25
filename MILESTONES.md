# RogueForge roadmap

RogueForge is being developed as a local-first Docker/Podman operations platform. The roadmap reflects the actual shipped codebase and keeps normal Compose files as the source of truth.

## 0.6.x — Container operations foundation

Status: Complete

- [x] Rootless Podman and Docker socket connectivity.
- [x] Compose stack discovery and lifecycle controls.
- [x] Safe Compose editing with validation and backup.
- [x] Signed administrator sessions and CSRF protection.
- [x] Self-stack/self-container protection.
- [x] Per-container Start, Stop, Restart, Update, Recreate, Inspect, Logs and guarded Remove.
- [x] Compose-aware per-service updates.
- [x] Update checks and Update All.
- [x] CPU, memory and network usage.
- [x] Multi-select and bulk Start/Stop/Restart/Update/Recreate/Remove.
- [x] Sorting/filtering and restart-policy inspection.
- [x] Rootless Podman-aware installer/upgrader and stable FEILSBEASTSERVER defaults.

## 0.7.0 — Live logs and terminal

Status: Current release

- [x] Stream container logs in real time.
- [x] Pause/resume live log display.
- [x] Search/filter streamed log output.
- [x] Download captured live logs.
- [x] Authenticated container exec terminal.
- [x] Bash-to-`sh` shell auto-detection/fallback.
- [x] Tokenized terminal sessions with authenticated reads and CSRF-protected writes.
- [x] Automatic inactive-session cleanup.
- [x] Explicit terminal close/cleanup.
- [ ] Stream Compose command output in real time.
- [ ] Persist operational command/action history.
- [ ] Keep long-running actions resumable across UI navigation/reloads.
- [ ] Add cancellation where the underlying runtime supports it.
- [ ] Add terminal resize/PTY support for full-screen interactive applications.

## 0.7.x — Live operations polish

Priority: Immediate

- [ ] Add an Operations/Tasks drawer for active and recently completed actions.
- [ ] Stream Pull/Update/Recreate/Compose validation output.
- [ ] Add timestamps and severity highlighting to live logs.
- [ ] Add configurable line limits and follow-to-bottom toggle.
- [ ] Add copy-selection/copy-all terminal controls.
- [ ] Add configurable terminal idle timeout.
- [ ] Add command history navigation in terminal input.
- [ ] Add per-action duration and exit status.
- [ ] Add health-check state and health-history snippets to container cards.
- [ ] Add uptime/last-restart information directly to container rows/cards.
- [ ] Continue responsive/mobile polish.

## 0.8.0 — Stack management parity

Priority: High

- [ ] Create a new Compose stack from the UI.
- [ ] Clone an existing stack.
- [ ] Rename/move a stack safely.
- [ ] Delete/archive stack definitions with explicit confirmation.
- [ ] Edit `.env` files alongside Compose files.
- [ ] Validate environment interpolation before deployment.
- [ ] Display Compose services, networks, volumes and dependencies graphically.
- [ ] Per-service Start/Stop/Restart/Update/Recreate from the stack page.
- [ ] Pull + deploy workflow matching Dockge-style update behaviour.
- [ ] Roll back to previous Compose/config backups.
- [ ] Optional Git-backed stack source and change history.

## 0.9.0 — Images, volumes and networks

Priority: Medium

- [ ] Images page with used/unused status, size, age and digest.
- [ ] Pull, inspect and remove images safely.
- [ ] Prune preview before destructive cleanup.
- [ ] Volumes page with ownership, usage and attached containers.
- [ ] Network page with connected containers and addresses.
- [ ] Safe orphan detection for images, volumes and networks.
- [ ] Disk-usage dashboard for container storage.

## 1.0.0 — Stable operations release

Goal: Production-quality single-host container management.

- [ ] Unified action/event history.
- [ ] Persistent audit log for privileged actions.
- [ ] Health/diagnostic panel with actionable remediation hints.
- [ ] Robust error normalization for Podman and Docker.
- [ ] Recovery paths for interrupted upgrades/actions.
- [ ] Backup/restore of RogueForge configuration and auth state.
- [ ] Stable API contract and documented endpoints.
- [ ] Automated test coverage for auth, Podman, Docker and Compose actions.
- [ ] Release validation against rootless Podman and Docker hosts.
- [ ] Accessibility and responsive-layout pass.
- [ ] Complete branding/logo/favicon/app-icon package.

## 1.1 — Monitoring and notifications

- [ ] HTTP/HTTPS monitors.
- [ ] TCP, DNS and ping monitors.
- [ ] TLS certificate expiry monitoring.
- [ ] Container health/state monitors.
- [ ] Uptime history and response-time charts.
- [ ] Maintenance windows.
- [ ] Discord/webhook/email notification providers.
- [ ] Alert suppression and recovery notifications.
- [ ] Private status dashboard.

## 1.2 — Automation and maintenance

- [ ] Scheduled image-update checks.
- [ ] Optional scheduled container/stack updates.
- [ ] Maintenance windows for automated updates.
- [ ] Pre-update snapshots/backups where supported.
- [ ] Automatic rollback when a health check fails after update.
- [ ] Scheduled restart policies independent of container restart policy.
- [ ] Image/container cleanup policies with dry-run preview.
- [ ] Webhook-triggered deployments.

## 1.3 — Multi-host

- [ ] RogueForge agent with outbound-only control channel.
- [ ] Multiple Podman/Docker hosts in one UI.
- [ ] Host grouping and labels.
- [ ] Cross-host search and status overview.
- [ ] Per-host permissions and action scope.
- [ ] Secure agent enrolment and key rotation.
- [ ] Host connectivity/agent version health.

## 1.4 — Users, roles and governance

- [ ] Multiple local users.
- [ ] Administrator/operator/read-only roles.
- [ ] Per-host/per-stack permissions.
- [ ] Optional external authentication providers.
- [ ] Session management/revocation UI.
- [ ] Approval workflow for destructive operations.
- [ ] Expanded audit/event retention controls.

## Branding and Rogue Dashboard integration

RogueForge branding remains version-independent so the same assets can be reused by Rogue Dashboard and other Rogue services.

```text
static/branding/rogueforge-logo.svg       # canonical scalable RogueForge service logo
static/branding/favicon.svg               # repository fallback favicon
docs/assets/rogueforge-banner.png         # GitHub/documentation banner
```

The browser currently uses the RogueAssassin GitHub identity image for its favicon/touch icon. The webpage references the canonical RogueForge sidebar logo with a text fallback. Rogue Dashboard should reuse the canonical square/service artwork rather than maintaining a separate RogueForge design.

## Guiding principles

- Keep normal Compose files as the source of truth.
- Prefer service-aware Compose operations over destructive raw-container recreation.
- Support rootless Podman as a first-class runtime.
- Preserve Docker support without forcing Docker-specific architecture on Podman users.
- Make destructive actions explicit, authenticated and recoverable.
- Build single-host operations to production quality before multi-host complexity becomes the default.
