![RogueForge](docs/assets/rogueforge-banner.png)

# RogueForge

**A secure, local-first command centre for Docker and Podman Compose stacks.**

RogueForge discovers existing Compose projects and containers, shows runtime state, reads logs, edits Compose files with validation/backup, and performs authenticated lifecycle operations through the host container engine.

## Current base: 0.6.0

0.6.0 builds on the reliable 0.5.x rootless Podman/Compose foundation and expands individual-container management. The Containers page now supports state-aware Start/Stop/Restart controls, Inspect, Logs, Compose-aware Update/Recreate, guarded Remove operations and self-container protection.

The project roadmap has been realigned to the actual codebase. See [MILESTONES.md](MILESTONES.md) for the planned 0.6.x operations polish, 0.7 console/terminal work, 0.8 stack-management parity, 0.9 storage/runtime resources and the path to a production-quality 1.0 release.

## Current features

- Discover Docker or rootless Podman containers through the mounted Unix socket.
- Discover normal Compose files under the configured stacks directory without importing them into a proprietary database.
- Start, stop, restart, pull and recreate Compose projects.
- Start, stop and restart individual containers.
- Inspect individual container runtime/configuration information.
- Read individual container logs.
- Update and recreate Compose-managed services without unnecessarily rebuilding the complete stack.
- Guard container removal behind authentication and confirmation.
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

The repository already contains the permanent GitHub/documentation banner:

```text
docs/assets/rogueforge-banner.png
```

The web interface currently keeps a CSS/text RF fallback so branding can never prevent the management UI from loading. The canonical service-logo contract for future artwork is documented in [MILESTONES.md](MILESTONES.md): a version-independent square RogueForge logo will live under `static/branding/` and can be reused by Rogue Dashboard instead of maintaining a second design.

Planned stable paths are:

```text
static/branding/rogueforge-logo.png
static/branding/rogueforge-logo.svg
static/branding/rogueforge-wordmark.svg
static/branding/favicon.svg
static/branding/apple-touch-icon.png
```

This allows a future RogueForge logo to be dropped into the webpage and copied/uploaded into Rogue Dashboard without changing application code or tying the artwork to a release number.

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
