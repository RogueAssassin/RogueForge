# RogueForge Roadmap

RogueForge is a lightweight Docker/Podman media-stack operations manager. The roadmap prioritises reliable lifecycle control, excellent live logging, low runtime overhead, and tight RogueDashboard integration.

## 1.3.0 — Stable lifecycle and deployment baseline

Status: **release**

- [x] Verified Start, Stop, Restart, Recreate and Update workflows.
- [x] In-place stack updates with immutable image verification and rollback protection.
- [x] Per-stack lifecycle serialization so competing actions cannot race.
- [x] Operation timeout, cancellation, progress and persistent bounded history.
- [x] Lightweight on-demand live logs with bounded concurrent streams.
- [x] Docker and rootless Podman support.
- [x] Canonical deployment at `/opt/media-server/rogueforge`.
- [x] Sibling-stack discovery rooted at `/opt/media-server`.
- [x] Detailed administrator-reference `.env` with documented tuning controls.
- [x] Persistent authentication and operations data.
- [x] Dashboard/inventory caching and bounded engine-detail concurrency.
- [x] Images, volumes and networks inventory.
- [x] Transactional Compose and `.env` editor writes.
- [x] User-tested Start, Stop, Restart and Update lifecycle on the media host.

## 1.4.0 — Logging and operations visibility

Focus: make RogueForge a stronger lightweight replacement for standalone container-log tooling.

- [ ] Improve multi-container stack log navigation and filtering.
- [ ] Add fast search/filter within the active bounded log buffer.
- [ ] Improve timestamps, stream/source labels and reconnect visibility.
- [ ] Add clearer operation duration, step timing and failure summaries.
- [ ] Add export/download of a bounded diagnostic log snapshot without continuous indexing.
- [ ] Improve interrupted-operation recovery reporting after RogueForge/container restart.
- [ ] Add diagnostics for socket, Compose provider, discovery roots and stack writability.

## 1.5.0 — Stack management and update intelligence

Focus: safer administration without adding background load.

- [ ] Add clearer per-stack image/update state and current image identity.
- [ ] Improve update preview so administrators can see affected services before applying.
- [ ] Add optional guarded bulk stack update workflow with strict serialization.
- [ ] Improve stopped-stack discovery and recovery edge cases.
- [ ] Expand Docker/rootless Podman lifecycle regression coverage.
- [ ] Improve Compose validation feedback before configuration changes are committed.

## 1.6.0 — RogueDashboard integration

Focus: make RogueForge and RogueDashboard operate as one clean media-management experience.

- [ ] Expand compact health/status endpoints for RogueDashboard.
- [ ] Surface lifecycle operation state and recent failures cleanly in RogueDashboard.
- [ ] Share consistent service identity/icon metadata.
- [ ] Add lightweight alert/event hooks for meaningful lifecycle failures.
- [ ] Validate whether RogueForge + RogueDashboard fully replace Dozzle for normal operations.
- [ ] Validate monitoring coverage before considering removal of Uptime Kuma.

## 2.0.0 — Production operations platform

Focus: only larger changes that justify a major version.

- [ ] Formalise stable API contracts for external integrations.
- [ ] Add migration/version handling for persistent application state.
- [ ] Expand audit and role/permission capabilities if multi-user administration is needed.
- [ ] Evaluate multi-host support without compromising the lightweight single-host baseline.
- [ ] Publish compatibility/support guarantees for supported Docker and Podman versions.

## Engineering principles

Every roadmap release should preserve these rules:

- no permanent high-frequency polling when event/on-demand work is sufficient;
- no unbounded log indexing or operation-history growth;
- lifecycle operations must verify the resulting state rather than trusting command exit codes;
- updates must retain rollback/recovery protection;
- RogueForge must never depend on stale external media lock files for its own lifecycle serialization;
- Docker and rootless Podman remain first-class deployment targets;
- existing `.env` and persistent administrator data must survive upgrades;
- new features should earn their runtime cost and keep RogueForge responsive on a media server.
