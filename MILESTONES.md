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
- [x] Make Compose + `.env` saves transactional: validate, write atomically, and restore the previous file on failure.
- [ ] Stack create/import/clone workflows.
- [ ] Compose templates with preview before creation.
- [ ] Backup/rollback browser for recent stack configuration revisions.

### Repository and runtime consolidation
- [x] Consolidate version-named frontend assets into canonical `app.js` / `styles.css`.
- [x] Remove obsolete release-note/banner artifacts from the active repository tree.
- [x] Fold the remaining build-time runtime preparation transformations into canonical source and retire `tools/prepare_runtime.py`.

### Performance and reliability
- [x] Coalesce simultaneous dashboard refreshes so only one dashboard/engine refresh is in flight.
- [x] Add stale-while-revalidate server snapshots for Overview/Stacks/Runtime.
- [ ] Invalidate only affected stack/container cache entries after operations.
- [ ] Batch runtime stats and cap concurrent inspect/stats work.
- [x] Add timing diagnostics for dashboard build/request, container inventory and stats.
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

Status: **validated 0.9.1 baseline**

- [x] Roll testing version to 0.9.1.
- [x] Persist server-backed Operations history with explicit duration/result/failure metadata.
- [x] Transactional Compose/.env save + automatic restore on validation/write failure.
- [x] Verified stack update rollback backend foundation; recovery status is returned to Operations/API callers.
- [x] Coalesced dashboard refresh and stale-while-revalidate snapshots (completed in 0.9.2).
- [x] Security header foundation completed in 0.9.3; session/proxy and destructive-action guardrails remain.
- [ ] Guarded Images/Volumes/Networks lifecycle actions.

### Automation and observability

- [ ] Optional maintenance windows and scheduled stack update policies.
- [ ] Notification hooks for failed operations and unhealthy stacks.
- [ ] Exportable diagnostics bundle with secrets redacted.
- [ ] Lightweight health/event history for troubleshooting without becoming a monitoring platform.

## 0.9.2 — Performance, cache coherence and diagnostics

Status: **validated 0.9.2 baseline**

- [x] Roll testing version to 0.9.2.
- [x] Coalesce simultaneous browser dashboard requests into one in-flight request.
- [x] Add server-side dashboard stale-while-revalidate snapshots for Overview/Stacks/Runtime.
- [x] Force-refresh controls explicitly bypass the dashboard snapshot.
- [x] Lifecycle inventory invalidation expires dashboard/resource snapshots.
- [x] Add rolling dashboard-build, dashboard-request, container-inventory and stats timing diagnostics.
- [ ] Add targeted stack/container cache invalidation instead of full inventory expiry.
- [ ] Add graceful partial dashboard responses when one engine query exceeds its latency budget.
- [ ] Bound concurrent stats/inspect work.
- [ ] Continue security/session hardening and guarded runtime-resource actions.

## 0.9.3 — Frontend consolidation and security hardening

Status: **current testing milestone**

- [x] Roll testing version to 0.9.3.
- [x] Replace duplicate dynamic operations/quality loading with one explicit frontend asset graph.
- [x] Fold runtime icon identity resolution into the canonical operations layer and remove the redundant quality script.
- [x] Remove active v0.8-era frontend labels/placeholders from canonical JavaScript.
- [x] Add security headers for framing, referrer leakage, browser permissions and cross-origin opener isolation.
- [x] Add regression guards for duplicate asset loading, stale active-script version labels and release metadata.
- [ ] Add graceful partial dashboard responses when one engine query exceeds its latency budget.
- [ ] Bound concurrent stats/inspect work.
- [ ] Harden reverse-proxy/session behavior and document trusted proxy expectations.
- [ ] Begin guarded Images/Volumes/Networks lifecycle controls after the safety contract is complete.

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
