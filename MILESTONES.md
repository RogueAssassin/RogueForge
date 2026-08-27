# RogueForge Roadmap

## 0.8.7 — Dashboard performance and verified lifecycle

Status: **validated testing baseline**

- [x] Unified initial dashboard snapshot.
- [x] Immediate browser session snapshot hydration with background refresh.
- [x] CPU/RAM refresh isolated from initial dashboard rendering.
- [x] Shared short-lived Podman inventory cache and reduced redundant engine calls.
- [x] Configurable media, Compose and environment roots.
- [x] Deterministic Podman Compose Start/Stop/Restart/Recreate/Update lifecycle.
- [x] Immutable image verification for update/replacement flows.
- [x] Permanent `main` / `testing` branch model and isolated GHCR testing channel.
- [x] CI validation, unit tests, local container build and GHCR `:testing` publish.

## 0.8.8 — Operations quality

Status: **current testing milestone**

- [ ] Stream long-running Pull/Update/Recreate output incrementally into the Operations drawer.
- [ ] Cancel supported long-running operations safely.
- [ ] Stack clone/import/create workflows.
- [ ] Compose templates and rollback UI.
- [x] Unified Dockge-style stack configuration editor with Compose / `.env` tabs, validation, automatic backups and save feedback.
- [x] Better service health visualization and stack health filtering.
- [ ] Server-side persistent operation/audit history shared across browsers.
- [ ] Preserve immediate/incremental UI state refresh after stack operations.
- [ ] Keep operation execution responsive and avoid full dashboard reloads where unnecessary.

## 0.9.0 — Runtime resources

- [ ] Image inventory and prune/update tools.
- [ ] Volume inventory, usage, backup/export and guarded deletion.
- [ ] Network inventory and membership management.
- [ ] Disk/storage visibility and cleanup recommendations.

## 1.0.0 — Stable single-host release

- [ ] Stable API contracts and migration policy.
- [ ] Expanded automated tests for Docker and rootless Podman.
- [ ] Backup/recovery and audit history.
- [ ] Hardened permissions, rate limiting and reverse-proxy guidance.
- [ ] Documented upgrade/rollback guarantees.

## Post-1.0

- Monitoring and notifications.
- Maintenance schedules and automatic update policies.
- Multi-host RogueForge agents.
- Multiple users, roles and permissions.
