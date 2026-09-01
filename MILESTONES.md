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
- [x] Cap concurrent inspect/stats engine-detail work (0.9.4).
- [x] Add timing diagnostics for dashboard build/request, container inventory and stats.
- [x] Return partial dashboard snapshots with degraded/error metadata when one engine/discovery query fails (0.9.4).

### Security and production hardening
- [x] Bound terminal/log sessions with idle/lifetime cleanup and per-process limits (0.9.4).
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
- [x] Add partial dashboard responses when an engine/discovery query fails (0.9.4).
- [x] Bound concurrent stats/inspect work (0.9.4).
- [ ] Continue security/session hardening and guarded runtime-resource actions.

## 0.9.3 — Frontend consolidation and security hardening

Status: **validated 0.9.3 baseline**

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

## 0.9.4 — Final production hardening

Status: **validated 0.9.4 baseline**

- [x] Roll testing version to 0.9.4.
- [x] Bound concurrent container inspect/stats engine-detail work.
- [x] Bound live terminal sessions with configurable idle and maximum lifetime limits.
- [x] Bound concurrent live-log streams and return an explicit 429 when capacity is exhausted.
- [x] Return partial dashboard data with degraded/error metadata when an engine/discovery query fails.
- [ ] Harden reverse-proxy/session behavior and document trusted proxy expectations.
- [ ] Add guarded Images/Volumes/Networks lifecycle actions.
- [ ] Add automated Docker and rootless Podman lifecycle compatibility checks.
- [ ] Finalize backup/recovery, upgrade and rollback guarantees for 1.0.

## 1.0.0-rc1 — Release candidate

Status: **validated release candidate**

- [x] Freeze the validated 0.9.4 feature baseline.
- [x] Roll testing version and deployment metadata to 1.0.0-rc1.
- [ ] Validate clean install on rootless Podman.
- [ ] Validate upgrade from 0.9.4 testing with configuration/data preservation.
- [ ] Validate rollback/recovery from RC1 to the previous known-good release.
- [ ] Validate Docker lifecycle parity for start/stop/restart/update/recreate.
- [ ] Validate rootless Podman lifecycle parity for start/stop/restart/update/recreate.
- [ ] Complete reverse-proxy/session deployment review.
- [ ] Complete guarded Images/Volumes/Networks lifecycle safety review.
- [ ] Run final production soak with no release-blocking errors.
- [ ] Final README/CHANGELOG/SECURITY/install/update audit before 1.0.0.

## 1.0.0 — Stable single-host release

Status: **production release**

- [x] Promote the validated 1.0.0-rc1 codebase without new feature changes.
- [x] Roll production version and deployment metadata to 1.0.0.
- [x] Preserve the validated Docker/Podman single-runtime architecture and 0.9.4 hardening baseline.
- [x] Finalize production README, changelog, install/update and GHCR metadata.

Status: **production release**

- [x] Promote the validated 1.0.0-rc1 codebase without new feature changes.
- [x] Roll production version and deployment metadata to 1.0.0.
- [x] Preserve the validated Docker/Podman single-runtime architecture and 0.9.4 hardening baseline.
- [x] Finalize production README, changelog, install/update and GHCR metadata.

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
