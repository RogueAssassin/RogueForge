# Changelog

## 2.3.0

- Promoted the testing line to production on top of the 2.0.1 hardening release.
- Service icons: RogueDashboard now shows its own dashboard-icons logo instead of the generic one, Pi-hole maps to `pi-hole`, PNG-only icons are tried after SVG, and RogueForge uses its bundled logo. Dropped the dead `/api/icons` and duplicate raw-GitHub fallbacks, and failed icon URLs are no longer re-requested on every re-render.
- Faster connects: container inventory now reads the engine API socket first (Docker and Podman alike) instead of spawning `podman --remote ps` per scan; set `ROGUEFORGE_INVENTORY_SOURCE=cli` to restore the old order. Each source falls back to the other.
- Fixed the inventory cache being stamped before the engine query ran, so a slow query expired it immediately and one dashboard build ran the query up to three times (about 4.4 s cold). Concurrent callers now share a single query.
- Added a background warmer (`ROGUEFORGE_DASHBOARD_WARM`, default 15 s, 0 disables) that keeps the dashboard snapshot inside the stale window, so the first visit after idle no longer waits for a cold scan.
- Moved the image to Debian trixie for the Podman 5.4 remote client. The previous 4.3 client made podman-compose skip `depends_on: condition: service_healthy` waits during in-app stack actions.
- Bumped the bundled Docker CLI to 29.9.0.

## 2.0.1

- Made `tini` PID 1 so `podman stop`/`docker stop` end RogueForge immediately and engine or Compose child processes are reaped.
- Bundled a static Docker CLI with the Compose v2 plugin so in-app stack actions work on Docker hosts; removed the unused Docker daemon from the image. The Podman remote client is unchanged.
- Replaced the bundled podman-compose 1.0.3 with 1.5.0. The old release failed every in-app action with `missing networks` on stacks whose services use network `aliases:` (RogueMediaValidator, RogueDashboard, RogueRoute GPX) and ignored `x-podman` and the `PODMAN_COMPOSE_*` settings RogueForge passes.
- Defined the health check in `compose.yaml` and added `no-new-privileges`, memory and PID ceilings, log rotation and a stop grace period.
- Added the optional `ROGUEFORGE_HOST_BIND`, `ROGUEFORGE_MEM_LIMIT` and `ROGUEFORGE_PIDS_LIMIT` settings; existing `.env` files keep working without them.
- Made `update.sh` pull before changing deployment files, take a lock, read the health port from `.env`, prune old backups and roll back the deployment files and image on failure.
- Fixed `install.sh` on Docker hosts where the shared network already exists.
- Added `.dockerignore`, Dependabot, least-privilege CI permissions, an image smoke test, build provenance and SBOM.

## 2.0.0 (testing)

- Established RogueForge API version 2 and persistent-state schema version 1.
- Added stable read-only `/api/v2/status` and `/api/v2/contract` endpoints.
- Added API/state contract metadata to the RogueDashboard integration payload.
- Declared backward compatibility from the validated 1.9.0 state baseline; no data migration is required for this testing candidate.
- Preserved the verified lifecycle, update preview, image verification, rollback, bounded logging, terminal and operation-history systems.
- Kept the default `.env` unchanged because 2.0.0 introduces no new runtime environment command.
- Kept 2.0.0 on the permanent `testing` branch pending live-host validation before main/latest promotion.

## 1.9.0 (testing)

- Established the final 1.x cleanup baseline before RogueForge 2.0.
- Removed no-op environment revision blocks and cleaned the repository for the major-version transition.

