# RogueForge Roadmap

RogueForge is the lightweight Docker/Podman management and troubleshooting layer for the Rogue media-server ecosystem.

## 1.9.0 — Pre-2.0 production cleanup

Status: **testing / main-promotion candidate**

- [x] Preserve verified Start, Stop, Restart, Recreate and Update workflows.
- [x] Preserve in-place image updates, immutable image verification and rollback.
- [x] Preserve update previews and strict lifecycle serialization.
- [x] Preserve bounded on-demand live logs, terminals and operation history.
- [x] Preserve the read-only RogueDashboard integration without another engine poller.
- [x] Keep `/opt/media-server/rogueforge` as the canonical deployment layout.
- [x] Keep the uploaded/default `.env` as the single fresh-install reference.
- [x] Remove Rev blocks that contain no actual new environment commands.
- [x] Remove no-op revision writes from `update.sh`.
- [x] Clean release documentation and historical version noise.
- [x] Freeze new 1.x features in preparation for 2.0.
- [ ] Complete final live-host regression/soak validation.
- [ ] Promote 1.9.0 from `testing` to `main`/latest once final validation is clean.

## 2.0.0 — Stable operations platform

Planned focus:

- stable, explicitly versioned external API contracts;
- persistent-state schema/version migrations;
- clearer integration contracts for RogueDashboard and other Rogue services;
- stronger structured audit/event data without unbounded history;
- final Dozzle replacement validation for normal single-host operations;
- explicit supported Docker/Podman compatibility policy;
- multi-host evaluation only if it can preserve the lightweight single-host baseline.

## Environment revision policy

`.env.example` is always the complete fresh-install default.

Existing installs keep their current `.env`. A revision block is added only when a release introduces one or more actual new environment settings. Releases with no environment changes add no Rev marker and the updater writes nothing to the file.

## Engineering principles

- verify resulting runtime state rather than trust command exit codes;
- retain update verification and rollback/recovery;
- no stale external media-lock dependency;
- no unnecessary permanent engine polling;
- no unbounded logs, terminals or operation history;
- preserve administrator configuration and persistent data across upgrades;
- Docker and rootless Podman remain first-class;
- new features must justify their CPU, memory, storage and engine-call cost.
