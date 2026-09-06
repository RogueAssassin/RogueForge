# RogueForge Roadmap

RogueForge is the lightweight Docker/Podman management and troubleshooting layer for the Rogue media-server ecosystem. New features must preserve verified lifecycle safety and exceptional idle performance.

## 1.5.0 — Stack management and update intelligence

Status: **testing release**

- [x] Preserve the host-tested Start, Stop, Restart, Recreate and Update lifecycle baseline.
- [x] Show a pre-update preview before stack updates.
- [x] Show affected running services and their configured image references.
- [x] Show current running image IDs and locally tagged image IDs.
- [x] Highlight locally available image changes without background pulling.
- [x] Keep the actual update path protected by pull, in-place recreate, verification and rollback.
- [x] Keep strict per-stack lifecycle serialization.
- [x] Preserve lightweight 1.4 live logging and bounded operation history.
- [x] Keep `.env.example` as the complete fresh-install default.
- [x] Introduce append-only environment revision blocks beginning with `Rev 150 update`.
- [x] Preserve existing administrator `.env` files during upgrades.

## 1.6.0 — RogueDashboard integration and migration validation

- [ ] Expand compact read-only status endpoints for RogueDashboard.
- [ ] Surface active operations and recent failures without exposing administrator credentials.
- [ ] Share consistent Rogue service identity/icon metadata.
- [ ] Add lightweight event hooks for meaningful lifecycle failures.
- [ ] Add clearer update/recovery summaries suitable for RogueDashboard.
- [ ] Complete live-host validation that RogueForge + RogueDashboard replace normal Dozzle workflows.
- [ ] Keep Uptime Kuma removal as a separate RogueDashboard monitoring-readiness decision.

## 1.7.0 — Operations quality

- [ ] Improve stack-level multi-service log navigation without creating a background index.
- [ ] Add bounded diagnostic bundles for support/troubleshooting.
- [ ] Improve interrupted-operation recovery reporting after RogueForge restarts.
- [ ] Add clearer socket, Compose-provider, discovery-root and writability diagnostics.
- [ ] Improve stopped-stack discovery and recovery edge cases.
- [ ] Expand Docker and rootless Podman lifecycle regression coverage.
- [ ] Improve Compose validation feedback before transactional saves.

## 2.0.0 — Stable operations platform

- [ ] Formalise stable external API contracts.
- [ ] Add explicit migration/version handling for persistent application state.
- [ ] Expand audit/role controls only if multi-user administration requires them.
- [ ] Evaluate multi-host support without compromising the single-host lightweight baseline.
- [ ] Publish explicit Docker/Podman compatibility guarantees.

## Environment revision policy

`.env.example` is always the complete default configuration for a fresh install.

Existing installations keep their current `.env`. If a later release introduces new environment commands, the release notes and updater add only a clearly labelled block:

```env
# ------------------------------------------------------------------------------
# Rev 160 update - RogueForge v1.6.0
# ------------------------------------------------------------------------------
NEW_SETTING=value
ROGUEFORGE_ENV_REV=160
```

This avoids replacing working administrator configuration just to introduce new settings.

## Engineering principles

- no permanent high-frequency engine polling when event/on-demand work is sufficient;
- no unbounded log indexing, terminal sessions or operation-history growth;
- lifecycle actions must verify the resulting state rather than trust command exit codes;
- updates must retain image verification and rollback/recovery protection;
- RogueForge must use its own lifecycle serialization rather than stale host lock files;
- Docker and rootless Podman remain first-class;
- existing `.env`, authentication and operation data survive upgrades;
- new environment settings use append-only revision blocks;
- every new feature must justify its CPU, memory, storage and engine-call cost.
