![RogueForge](docs/assets/rogueforge-banner.png)

# RogueForge

**A secure, local-first command centre for Docker and Podman Compose stacks.**

RogueForge discovers existing Compose projects and containers, shows runtime state, edits Compose files safely, manages container/stack lifecycle, streams logs, and provides authenticated container terminal access through the host container engine.

## Current release: 0.7.0

0.7.0 adds the live-operations layer on top of the stable 0.6.2 container-management base. Running containers now expose **Live logs** and **Terminal** controls. Live logs stream through authenticated Server-Sent Events with pause, filtering, clear and download controls. Terminal sessions use authenticated container exec with Bash-to-`sh` fallback, CSRF-protected input/close operations, process-exit tracking and automatic idle cleanup.

See [MILESTONES.md](MILESTONES.md) for the remaining 0.7.x live-operation polish, 0.8 stack-management parity, 0.9 storage/runtime resources, and the path to 1.0.

## Current features

- Docker and rootless Podman through a mounted Unix socket.
- Compose stack discovery without importing stack definitions into a proprietary database.
- Stack Start, Stop, Restart, Pull, Recreate and validated Compose editing.
- Container Start, Stop, Restart, Update, Recreate, Inspect, Logs and guarded Remove.
- Compose-aware per-service updates and recreation.
- Multi-select bulk Start/Stop/Restart/Update/Recreate/Remove.
- Update checks and Update All while excluding RogueForge itself.
- CPU, memory and network usage.
- Sorting/filtering plus restart-policy inspection.
- Authenticated live container logs with pause/search/download.
- Authenticated container terminal/exec with shell fallback and automatic cleanup.
- Signed administrator sessions, CSRF protection and login throttling.
- Self-stack and self-container protection.
- Nginx Proxy Manager support on shared `media-net`.
- Multi-architecture GHCR publishing.
- Runtime-aware upgrades with deployment backup/rollback.

## FEILSBEASTSERVER / default rootless Podman layout

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

The installer derives the rootless Podman socket UID from the user running it. UID 1000 is the repository/default example.

## Branding

The permanent repository banner is:

```text
docs/assets/rogueforge-banner.png
```

Canonical application branding lives under:

```text
static/branding/rogueforge-logo.svg
static/branding/favicon.svg
```

The browser favicon/touch icon currently uses the RogueAssassin GitHub identity image. The sidebar uses the RogueForge service logo with a text fallback. Rogue Dashboard can later reuse the same canonical service artwork.

## First installation

Requirements:

- Linux with rootless Podman or Docker.
- `podman-compose` for Podman, or Docker Compose for Docker.
- Python 3, `curl`, Git and `sudo`.
- Run installation as the account that owns the containers, not root.

```bash
cd /tmp
git clone --branch v0.7.0 --depth 1 \
  https://github.com/RogueAssassin/RogueForge.git rogueforge-install-0.7.0
cd rogueforge-install-0.7.0
chmod +x install.sh
./install.sh --engine podman
```

## Existing installation: upgrade

To follow the current `main`/`latest` development image:

```bash
cd /opt/media-server/rogueforge
./upgrade.sh latest
```

For the immutable semantic release once the `v0.7.0` tag/image is published:

```bash
cd /opt/media-server/rogueforge
./upgrade.sh 0.7.0
```

The upgrader preserves `.env` and `data/auth.json`, backs up the deployment, refreshes matching deployment files, validates Compose, recreates RogueForge and verifies `/health`.

## Login and password recovery

The default username is `administrator`.

```bash
cd /opt/media-server/rogueforge
python3 setup-auth.py --username administrator
podman-compose restart
```

## Nginx Proxy Manager

| Setting | Value |
| --- | --- |
| Domain | `manage.roguegaming.com.au` |
| Scheme | `http` |
| Forward hostname | `rogueforge` |
| Forward port | `7810` |
| WebSockets | enabled |
| Block Common Exploits | enabled |
| Force SSL | enabled after certificate issuance |

NPM and RogueForge must both be attached to `media-net`. For live logs, proxy buffering should remain disabled; RogueForge also sends `X-Accel-Buffering: no` on the SSE stream.

## Security notes for terminal access

Terminal access requires an authenticated administrator session. Creating a terminal, sending input and closing the terminal are CSRF-protected. Sessions are held only in RogueForge memory, close when the exec process exits, and expire after inactivity. RogueForge does not expose terminal sessions without authentication.

## Documentation

- [Roadmap](MILESTONES.md)
- [Installation and reverse proxy](docs/INSTALL.md)
- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
- [GHCR publishing](docs/GHCR.md)
- [Security model](SECURITY.md)
- [Release history](CHANGELOG.md)

## Acknowledgements

Dockge and Uptime Kuma are product inspirations. RogueForge is an original implementation and does not copy their source code or branding.
