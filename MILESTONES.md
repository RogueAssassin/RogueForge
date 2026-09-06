# RogueForge Roadmap

RogueForge is the lightweight Docker/Podman management and troubleshooting layer for the Rogue media-server ecosystem. New features must preserve verified lifecycle safety and exceptional idle performance.

## 1.4.0 — Logging and operations visibility

Status: **testing release**

- [x] Preserve the host-tested Start, Stop, Restart, Recreate and Update lifecycle baseline.
- [x] Keep per-stack lifecycle serialization and update rollback protection.
- [x] Add fast text search inside the bounded live-log buffer.
- [x] Add Error, Warning and Info live-log severity filters.
- [x] Add clearer stream source and reconnect-attempt visibility.
- [x] Keep pause/resume buffering and bounded log downloads.
- [x] Keep server-side logging on demand with no persistent log indexer.
- [x] Show operation duration, current step, step elapsed time, timeout and failure reason.
- [x] Keep bounded JSON operation-history export.
- [x] Keep canonical deployment at `/opt/media-server/rogueforge`.
- [x] Keep detailed administrator `.env` documentation aligned with RogueMediaValidator.
- [x] Keep GitHub release presentation aligned with RogueDashboard and RogueMediaValidator.

## 1.5.0 — Stack management and update intelligence

- [ ] Show clearer current/pulled image identity before applying an update.
- [ ] Add an update preview showing affected stack services.
- [ ] Add guarded multi-stack update with strict per-stack serialization.
- [ ] Improve stopped-stack discovery and recovery edge cases.
- [ ] Expand Docker and rootless Podman lifecycle regression coverage.
- [ ] Improve Compose validation feedback before transactional saves.
- [ ] Add clearer update/recovery summaries suitable for RogueDashboard.

## 1.6.0 — RogueDashboard integration and migration validation

- [ ] Expand compact read-only status endpoints for RogueDashboard.
- [ ] Surface active operations and recent failures without exposing administrator credentials.
- [ ] Share consistent Rogue service identity/icon metadata.
- [ ] Add lightweight event hooks for meaningful lifecycle failures.
- [ ] Complete live-host validation that RogueForge + RogueDashboard replace normal Dozzle workflows.
- [ ] Keep Uptime Kuma removal as a separate RogueDashboard monitoring-readiness decision.

## 1.7.0 — Operations quality

- [ ] Improve stack-level multi-service log navigation without creating a background index.
- [ ] Add bounded diagnostic bundles for support/troubleshooting.
- [ ] Improve interrupted-operation recovery reporting after RogueForge restarts.
- [ ] Add clearer socket, Compose-provider, discovery-root and writability diagnostics.
- [ ] Review runtime resource inventory for safe guarded maintenance actions.

## 2.0.0 — Stable operations platform

- [ ] Formalise stable external API contracts.
- [ ] Add explicit migration/version handling for persistent application state.
- [ ] Expand audit/role controls only if multi-user administration requires them.
- [ ] Evaluate multi-host support without compromising the single-host lightweight baseline.
- [ ] Publish explicit Docker/Podman compatibility guarantees.

## Engineering principles

- no permanent high-frequency engine polling when event/on-demand work is sufficient;
- no unbounded log indexing, terminal sessions or operation-history growth;
- lifecycle actions must verify the resulting state rather than trust command exit codes;
- updates must retain image verification and rollback/recovery protection;
- RogueForge must use its own lifecycle serialization rather than stale host lock files;
- Docker and rootless Podman remain first-class;
- existing `.env`, authentication and operation data survive upgrades;
- every new feature must justify its CPU, memory, storage and engine-call cost.
