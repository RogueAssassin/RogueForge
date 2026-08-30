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

## 0.9.0 — Operations quality, performance and production readiness

Status: **validated 0.9.0 baseline**

### Operations and recovery
- [ ] Stream Pull/Update/Recreate output incrementally into the Operations drawer.
- [x] Add bounded operation timeouts and explicit timeout/recovery states.
- [x] Cancel supported long-running operations safely.
- [x] Persist operation/audit history server-side so it survives browser/container restarts.
- [x] Record target, operation type, start/end time, duration, result and concise failure reason.
- [ ] Add verified rollback/recovery UX when an update or recreate fails.
- [ ] Keep immediate targeted UI refresh after stack operations without a full dashboard reload.

### Stack authoring
- [x] Unified Dockge-style Compose / `.env` editor with validation, automatic backups and save feedback.
- [ ] Make Compose + `.env` saves transactional: validate first, write atomically, restore on failure.
- [ ] Stack create/import/clone workflows.
- [ ] Compose templates with preview before creation.
- [ ] Backup/rollback browser for recent stack configuration revisions.

### Repository and runtime consolidation
- [x] Consolidate version-named frontend assets into canonical `app.js` / `styles.css`.
- [x] Remove obsolete release-note/banner artifacts from the active repository tree.
- [x] Fold the remaining build-time runtime preparation transformations into canonical source and retire `tools/prepare_runtime.py`.

### Performance and reliability
- [ ] Coalesce simultaneous dashboard refreshes so only one engine inventory refresh is in flight.
- [ ] Add stale-while-revalidate server snapshots for Overview/Stacks/Runtime.
- [ ] Invalidate only affected stack/container cache entries after operations.
- [ ] Batch runtime stats and cap concurrent inspect/stats work.
- [ ] Add endpoint timing diagnostics for dashboard, stacks, containers and stats.
- [ ] Add graceful degradation when one engine/stack query is slow rather than blocking the full dashboard.

### Security and production hardening
- [ ] Bound terminal/log sessions with idle cleanup and per-session limits.
- [ ] Review authentication/session cookie defaults for reverse-proxy deployments.
- [ ] Add security headers and document trusted-proxy behaviour.
- [ ] Add explicit destructive-operation confirmation/guardrails for remove/prune workflows.
- [ ] Expand regression tests for rootless Podman and Docker lifecycle/update paths.

### Runtime resources

- [x] Image inventory foundation with container usage relationships.
- [ ] Image update awareness and guarded prune tools.
- [x] Volume inventory foundation with container mount relationships.
- [ ] Volume usage, backup/export and guarded deletion.
- [x] Network inventory foundation with container membership relationships.
- [ ] Network membership management and guarded lifecycle controls.
- [ ] Disk/storage visibility and cleanup recommendations.
- [x] Resource pages reuse cached engine snapshots and explicit refresh bypasses the resource cache.

## 0.9.1 — Safety, recovery and observability

Status: **current testing milestone**

- [x] Roll testing version to 0.9.1.
- [x] Persist server-backed Operations history with explicit duration/result/failure metadata.
- [ ] Transactional Compose/.env save + automatic restore on validation/write failure.
- [ ] Verified update/recreate rollback UX.
- [ ] Coalesced dashboard refresh and stale-while-revalidate snapshots.
- [ ] Security header/session hardening and destructive-action guardrails.
- [ ] Guarded Images/Volumes/Networks lifecycle actions.

### Automation and observability

- [ ] Optional maintenance windows and scheduled stack update policies.
- [ ] Notification hooks for failed operations and unhealthy stacks.
- [ ] Exportable diagnostics bundle with secrets redacted.
- [ ] Lightweight health/event history for troubleshooting without becoming a monitoring platform.

## 1.0.0 — Stable single-host release

- [ ] Stable API contracts and migration policy.
- [ ] Automated Docker and rootless Podman compatibility matrix.
- [ ] Documented backup/recovery, upgrade and rollback guarantees.
- [ ] Persistent audit history and recovery workflows.
- [ ] Hardened permissions, rate limiting and reverse-proxy guidance.
- [ ] Release-candidate soak testing on the permanent `testing` channel.

## Post-1.0

- Multi-host RogueForge agents.
- Multiple users, roles and permissions.
- Broader notification/integration ecosystem.
