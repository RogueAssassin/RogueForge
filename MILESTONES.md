# RogueForge Roadmap

## 0.8.3 — Operations quality foundation

Status: **current testing/release line**

- [x] Single `rogueforge.py` backend runtime retained.
- [x] Update backups moved outside the stack discovery tree with legacy migration.
- [x] Persistent Operations activity drawer for stack/container mutations.
- [x] Operation history with success/failure details, timestamps, duration and captured output.
- [x] Resilient Dashboard Icons resolver with exact Nginx Proxy Manager and Cloudflared aliases.
- [x] GHCR release aliases: `latest`, semantic, v-prefixed, compact and SHA tags.
- [x] Automatic Git release-tag creation for new versions.

## 0.8.x — Operations quality

- [ ] Stream long-running Pull/Update/Recreate output incrementally into the Operations drawer.
- [ ] Cancel supported long-running operations safely.
- [ ] Stack clone/import/create workflows.
- [ ] Compose templates and rollback UI.
- [ ] Better service health/dependency visualization.
- [ ] Server-side persistent operation/audit history shared across browsers.

## 0.9.0 — Runtime resources

- [ ] Image inventory and prune/update tools.
- [ ] Volume inventory, usage, backup/export and guarded deletion.
- [ ] Network inventory and membership management.
- [ ] Disk/storage visibility and cleanup recommendations.

## 1.0.0 — Stable single-host release

- [ ] Stable API contracts and migration policy.
- [ ] Expanded automated tests for Docker and rootless Podman.
- [ ] Backup/recovery and audit history.
- [ ] Hardened permissions, rate limiting and reverse-proxy guidance.
- [ ] Documented upgrade/rollback guarantees.

## Post-1.0

- Monitoring and notifications.
- Maintenance schedules and automatic update policies.
- Multi-host RogueForge agents.
- Multiple users, roles and permissions.
