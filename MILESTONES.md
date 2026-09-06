# RogueForge Roadmap

RogueForge is the lightweight Docker/Podman management and troubleshooting layer for the Rogue media-server ecosystem. New features must preserve verified lifecycle safety and exceptional idle performance.

## 1.6.0 — RogueDashboard integration and migration validation

Status: **testing release**

- [x] Preserve the host-tested lifecycle, update preview, rollback and logging baseline.
- [x] Add a compact read-only RogueDashboard integration endpoint.
- [x] Expose version, engine type, stack/container counts and capability flags.
- [x] Expose active operation count/items and recent failure summaries without raw output.
- [x] Reuse RogueForge's existing cached dashboard snapshot instead of adding another engine poller.
- [x] Keep engine socket paths, Compose paths and administrator credentials out of the integration payload.
- [x] Adopt the uploaded default `.env` layout as the canonical fresh-install reference.
- [x] Preserve revision history and append `Rev 160 update` at the bottom.
- [x] Keep existing administrator `.env` files intact during upgrades.

## 1.7.0 — Operations quality

- [ ] Improve stack-level multi-service log navigation without creating a background index.
- [ ] Add bounded diagnostic bundles for support/troubleshooting.
- [ ] Improve interrupted-operation recovery reporting after RogueForge restarts.
- [ ] Add clearer socket, Compose-provider, discovery-root and writability diagnostics.
- [ ] Improve stopped-stack discovery and recovery edge cases.
- [ ] Expand Docker and rootless Podman lifecycle regression coverage.
- [ ] Improve Compose validation feedback before transactional saves.
- [ ] Complete live-host validation that RogueForge + RogueDashboard replace normal Dozzle workflows.

## 2.0.0 — Stable operations platform

- [ ] Formalise stable external API contracts.
- [ ] Add explicit migration/version handling for persistent application state.
- [ ] Expand audit/role controls only if multi-user administration requires them.
- [ ] Evaluate multi-host support without compromising the single-host lightweight baseline.
- [ ] Publish explicit Docker/Podman compatibility guarantees.

## Environment revision policy

`.env.example` is always the complete default configuration for a fresh install and follows the uploaded canonical layout.

Existing installations keep their current `.env`. New settings are added only as revision blocks at the bottom:

```env
# ------------------------------------------------------------------------------
# Rev 170 update - RogueForge v1.7.0
# ------------------------------------------------------------------------------
NEW_SETTING=value
ROGUEFORGE_ENV_REV=170
```

If a release requires no new runtime setting, its revision block contains only the revision marker and explanatory comments.

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
