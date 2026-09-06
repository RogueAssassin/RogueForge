# RogueForge Roadmap

## 2.0.0 — Stable operations platform

Status: **testing / main-promotion candidate**

- [x] Preserve the validated 1.9 lifecycle, update, logging and terminal baseline.
- [x] Establish explicit API version 2.
- [x] Establish persistent-state schema version 1.
- [x] Add stable read-only `/api/v2/status`.
- [x] Add `/api/v2/contract` with compatibility/state metadata.
- [x] Align RogueDashboard integration output with the v2 contract.
- [x] Preserve existing 1.9 persistent state without a forced migration.
- [x] Add no `.env` revision because 2.0 introduces no new runtime setting.
- [x] Keep Docker and rootless Podman first-class.
- [ ] Complete live-host 2.0 regression/soak validation.
- [ ] Promote 2.0.0 to `main` / `:latest` after testing passes.
- [ ] Immediately advance `testing` to 2.1.0 after production promotion.

## 2.1.0 — Post-2.0 development

Planned after 2.0 promotion:

- expand versioned API coverage for external integrations;
- improve structured audit/event records while keeping history bounded;
- strengthen diagnostics and interrupted-operation recovery reporting;
- continue Dozzle replacement validation;
- add only environment revision blocks that introduce real settings.

## Environment revision policy

`.env.example` remains the complete fresh-install default. Existing installs keep their current `.env`. Releases with no new settings add no Rev marker.

## Engineering principles

- verify resulting state, not just command exit codes;
- preserve rollback/recovery;
- no unnecessary permanent polling;
- no unbounded logs, terminals or operation history;
- preserve administrator configuration and persistent state;
- Docker and rootless Podman remain first-class;
- new features must justify their runtime cost.
