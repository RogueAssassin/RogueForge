# RogueForge Roadmap

## 2.0.0 — Stable operations platform

Status: **released to main / latest**

- [x] Preserve the validated 1.9 lifecycle, update, logging and terminal baseline.
- [x] Establish API version 2 and state schema version 1.
- [x] Add stable read-only `/api/v2/status` and `/api/v2/contract`.
- [x] Align RogueDashboard integration with the v2 contract.
- [x] Complete live-host validation.
- [x] Promote 2.0.0 to `main` / `:latest`.

## 2.1.0 — Post-2.0 development

Status: **active testing**

Planned focus:

- expand versioned read-only API coverage for external integrations;
- improve structured audit/event records while keeping history bounded;
- strengthen diagnostics and interrupted-operation recovery reporting;
- continue RogueDashboard/RogueForge integration quality;
- continue Dozzle replacement validation;
- add only environment revision blocks that introduce real settings;
- preserve exceptional idle performance and the validated lifecycle/update baseline.

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
