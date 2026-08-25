# RogueForge Roadmap

## 0.8.2 — Consolidated runtime

Status: **current testing/release line**

- [x] Single `rogueforge.py` backend runtime.
- [x] Remove version-specific runtime wrappers/extensions.
- [x] Stack-first Compose management.
- [x] Flexible recursive Compose discovery.
- [x] Compose and `.env` editing with backup/validation.
- [x] Service/container lifecycle and bulk runtime controls.
- [x] Live logs and authenticated terminal/exec.
- [x] Dashboard Icons service artwork with local fallback.
- [x] Approved RogueForge Base/Dark/Light branding.
- [x] Clean `update.sh` and CI workflow.

## 0.8.x — Operations quality

- Stream Pull/Update/Recreate output into an Operations drawer.
- Operation history with success/failure details and timestamps.
- Cancel supported long-running operations safely.
- Stack clone/import/create workflows.
- Compose templates and rollback UI.
- Better service health/dependency visualization.

## 0.9.0 — Runtime resources

- Image inventory and prune/update tools.
- Volume inventory, usage, backup/export and guarded deletion.
- Network inventory and membership management.
- Disk/storage visibility and cleanup recommendations.

## 1.0.0 — Stable single-host release

- Stable API contracts and migration policy.
- Expanded automated tests for Docker and rootless Podman.
- Backup/recovery and audit history.
- Hardened permissions, rate limiting and reverse-proxy guidance.
- Documented upgrade/rollback guarantees.

## Post-1.0

- Monitoring and notifications.
- Maintenance schedules and automatic update policies.
- Multi-host RogueForge agents.
- Multiple users, roles and permissions.
