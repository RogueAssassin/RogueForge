![RogueForge](docs/assets/rogueforge-banner.png)

# RogueForge

**A secure, local-first command centre for Docker and Podman Compose stacks.**

RogueForge discovers existing Compose projects and containers, shows runtime state, reads logs, edits Compose files with validation/backup, and performs authenticated lifecycle operations through the host container engine.

## Current base: 0.6.2

0.6.2 builds on the reliable 0.5.x rootless Podman/Compose foundation and the 0.6.x container-management work. The Containers page now supports state-aware Start/Stop/Restart, Inspect, Logs, Compose-aware Update/Recreate, guarded Remove operations, live resource usage, image update checks, Update All, sorting, multi-select bulk actions, restart-policy inspection, and self-container protection.

The project roadmap is maintained in [MILESTONES.md](MILESTONES.md), covering the remaining 0.6.x operations polish, 0.7 console/terminal work, 0.8 stack-management parity, 0.9 storage/runtime resources and the path to a production-quality 1.0 release.

## Current features

- Discover Docker or rootless Podman containers through the mounted Unix socket.
- Discover normal Compose files under the configured stacks directory without importing them into a proprietary database.
- Start, stop, restart, pull and recreate Compose projects.
- Start, stop, restart, update, recreate, inspect, log and remove individual containers/services where safe.
- Apply bulk Start, Stop, Restart, Update, Recreate and Remove operations to selected manageable containers.
- Display live CPU, memory and network usage.
- Check pulled image state against the image used by a running container.
- Update all manageable containers while excluding RogueForge itself.
- Sort and filter containers by name, state, project and image.
- Inspect restart policy, runtime timestamps, image IDs, mounts, networks and service metadata.
- Update and recreate Compose-managed services without unnecessarily rebuilding the complete stack.
- Edit Compose files with automatic backup and validation before changes are accepted.
- Protect privileged operations with signed administrator sessions and CSRF validation.
- Protect RogueForge's own Compose project/container from self-destructive lifecycle operations.
- Reuse local Rogue Dashboard-compatible service icons.
- Run behind Nginx Proxy Manager on the shared `media-net` network.
- Pull multi-architecture images from GHCR.
- Upgrade image and deployment files together with rollback backups.

## FEILSBEASTSERVER / default rootless Podman layout

The supported production defaults are:

```text
Container owner UID:  1000
Stacks root:          /opt/media-server
RogueForge install:   /opt/media-server/rogueforge
Podman socket source: /run/user/1000/podman/podman.sock
Socket in container:  /run/podman/podman.sock
LAN port:             17810
Container port:       7810
Shared network:       media-net
Public URL:           https://manage.roguegaming.com.au
Account file:         /opt/media-server/rogueforge/data/auth.json
```

The installer derives the Podman socket UID dynamically from the user running it. UID 1000 is only the repository/example default.

## Branding

The permanent GitHub/documentation banner remains:

```text
docs/assets/rogueforge-banner.png
```

The browser favicon and touch icon now use the RogueAssassin GitHub profile identity image. The application sidebar has a stable RogueForge-specific logo with a text fallback, and future shared RogueForge/Rogue Dashboard artwork remains version-independent under:

```text
static/branding/rogueforge-logo.svg
static/branding/favicon.svg
```

This keeps web identity independent from release numbers and leaves a clean path for Rogue Dashboard to reuse the same RogueForge service artwork later.

## Installation and upgrades

Run the installer/upgrader as the user that owns the rootless Podman or Docker containers, not as root.

To follow the current development release:

```bash
cd /opt/media-server/rogueforge
./upgrade.sh latest
```

The upgrader preserves `.env` and `data/auth.json`, backs up the deployment, pulls the target image first, refreshes the matching deployment bundle, validates Compose, recreates RogueForge and verifies `/health`.

## Login and password recovery

The default username is `administrator`.

Reset the password and invalidate existing sessions with:

```bash
cd /opt/media-server/rogueforge
python3 setup-auth.py --username administrator
podman-compose restart
```

Authentication data remains in `data/auth.json`.

## Nginx Proxy Manager

Use:

| Setting | Value |
| --- | --- |
| Domain | `manage.roguegaming.com.au` |
| Scheme | `http` |
| Forward hostname | `rogueforge` |
| Forward port | `7810` |
| WebSockets | enabled |
| Block Common Exploits | enabled |
| Force SSL | enabled after certificate issuance |

NPM and RogueForge must both be attached to `media-net`.

## Documentation

- [Roadmap](MILESTONES.md)
- [Installation and reverse proxy](docs/INSTALL.md)
- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
- [GHCR publishing](docs/GHCR.md)
- [Security model](SECURITY.md)
- [Release history](CHANGELOG.md)

## Acknowledgements

Dockge and Uptime Kuma are product inspirations. RogueForge is an original implementation and does not copy their source code or branding.
