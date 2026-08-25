# RogueForge roadmap

RogueForge is being developed as a local-first Docker/Podman operations platform. The roadmap below reflects the actual 0.6.0 codebase rather than the older placeholder version numbering.

## 0.6.0 — Container operations foundation

Status: Current base

- [x] Rootless Podman and Docker socket connectivity.
- [x] Compose stack discovery and lifecycle controls.
- [x] Safe Compose editing with validation and backup.
- [x] Signed administrator sessions and CSRF protection.
- [x] Self-stack/self-container protection.
- [x] Per-container Start, Stop and Restart controls.
- [x] Per-container Logs and Inspect views.
- [x] Compose-aware per-service Update and Recreate actions.
- [x] Guarded container Remove action.
- [x] Rootless Podman-aware installer and upgrade path.
- [x] Stable FEILSBEASTSERVER deployment defaults.

## 0.6.x — Operations polish

Priority: Immediate

- [ ] Replace basic container table with richer responsive cards/table modes.
- [ ] Add live action output instead of toast-only completion messages.
- [ ] Add progress/busy states per container and per stack.
- [ ] Disable conflicting controls while an action is running.
- [ ] Add bulk selection and bulk Start/Stop/Restart/Update.
- [ ] Add Update All with Compose-aware grouping.
- [ ] Add image update-available detection and last-checked timestamps.
- [ ] Show current image digest, remote digest and update status.
- [ ] Add CPU, memory, network and block-I/O statistics.
- [ ] Add health-check state and health history snippets.
- [ ] Add restart policy, uptime, created time and last restart to container cards.
- [ ] Add sortable/filterable columns and state/project/image filters.
- [ ] Add container/stack favourites or pinning.
- [ ] Improve mobile/tablet layouts.
- [ ] Add keyboard-accessible dialogs and stronger action confirmations.

## 0.7.0 — Console, terminal and logs

Priority: High

- [ ] Stream Compose command output in real time.
- [ ] Stream container logs with pause/resume, follow and line limits.
- [ ] Search/filter/download log output.
- [ ] Add authenticated container exec terminal.
- [ ] Add shell auto-detection (`bash`, `sh`, etc.).
- [ ] Add command history for operational actions.
- [ ] Keep long-running actions alive safely across UI navigation.
- [ ] Add action cancellation where the underlying runtime supports it.

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
- [ ] Roll back to the previous Compose/config backup.
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

RogueForge branding must remain version-independent so the same assets can be reused by Rogue Dashboard and other Rogue services.

Canonical planned assets:

```text
static/branding/rogueforge-logo.png       # square transparent application/service logo
static/branding/rogueforge-logo.svg       # scalable source where available
static/branding/rogueforge-wordmark.svg   # horizontal RogueForge wordmark
static/branding/favicon.svg               # browser favicon
static/branding/apple-touch-icon.png      # 180x180 app icon
docs/assets/rogueforge-banner.png         # GitHub/documentation banner (already present)
```

The webpage should reference the canonical `/branding/rogueforge-logo.*` asset with a CSS/text fallback so a missing or replaced artwork file cannot break navigation. Rogue Dashboard should import/copy the same canonical square logo rather than maintaining a separate RogueForge-specific design.

## Guiding principles

- Keep normal Compose files as the source of truth.
- Prefer service-aware Compose operations over destructive raw-container recreation.
- Support rootless Podman as a first-class runtime, not a compatibility afterthought.
- Preserve Docker support without forcing Docker-specific architecture on Podman users.
- Make destructive actions explicit, authenticated and recoverable.
- Build single-host operations to production quality before making multi-host complexity the default.
