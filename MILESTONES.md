# RogueForge Roadmap

## 0.8.4 — Operations visibility and health

Status: **current testing/release line**

- [x] Canonical non-versioned `operations.js` / `operations.css` frontend quality layer.
- [x] Stack health filters for All, Healthy, Partial and Stopped workloads.
- [x] Stronger stack/service visual fault highlighting.
- [x] Operations history filtering by running/success/failed state.
- [x] Export Operations history as JSON for troubleshooting/support.
- [x] Resilient Dashboard Icons resolver retained with Nginx Proxy Manager and Cloudflared aliases.
- [x] Fix release workflow so the actual published container runtime is stamped with the `VERSION` value before the image build.
- [x] Keep semantic, v-prefixed, compact, latest and SHA GHCR aliases.

## 0.8.x — Operations quality

- [ ] Stream long-running Pull/Update/Recreate output incrementally into the Operations drawer.
- [ ] Cancel supported long-running operations safely.
- [ ] Stack clone/import/create workflows.
- [ ] Compose templates and rollback UI.
- [x] Better service health visualization and stack health filtering.
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
