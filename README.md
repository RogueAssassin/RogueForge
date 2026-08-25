![RogueForge](static/branding/rogueforge.svg)

# RogueForge

**A local-first operations console for Docker and Podman Compose.**

## Current release: 0.8.3

RogueForge 0.8.3 builds on the consolidated single-file backend with the first **Operations Quality** milestone features: a persistent Operations activity drawer, resilient Dashboard Icons resolution, cleaner update backups, and automatic release aliases for GHCR.

### What it manages

- Recursive Compose stack discovery from runtime labels, working-directory/config-file metadata, and filesystem scanning.
- Docker and rootless Podman through a mounted Unix socket.
- Stack Start, Stop, Restart, Pull, Recreate, and Update (`pull` + `up -d --remove-orphans`).
- Compose and `.env` editing with backups and runtime-aware validation.
- Service/container Start, Stop, Restart, Update, Recreate, Remove, Inspect, image checks, bulk actions, and resource statistics.
- Live logs over authenticated Server-Sent Events.
- Authenticated container terminal/exec sessions with Bash → `sh` fallback and automatic cleanup.
- RogueForge self-container/self-stack protection.
- Signed administrator sessions, CSRF protection, and login throttling.
- Centralized stack/service icons from [Dashboard Icons](https://dashboardicons.com/icons), with jsDelivr, raw-GitHub, local and generic fallbacks.
- Persistent browser-side Operations history for stack/container mutations with status, timestamps, duration and captured output.

## Repository layout

```text
rogueforge.py          # complete application runtime
VERSION                # release metadata
setup-auth.py          # administrator password maintenance
install.sh             # first installation
update.sh              # updates/releases
compose.yaml           # deployment
Containerfile          # image build
static/                # web interface and RogueForge branding
tests/                 # validation tests
docs/                  # deployment documentation
```

There are no versioned `rogueforge_v*.py` entry points and no runtime extension modules.

## FEILSBEASTSERVER / default rootless Podman layout

```text
Stacks root:          /opt/media-server
RogueForge install:   /opt/media-server/rogueforge
Podman socket source: /run/user/1000/podman/podman.sock
Socket in container:  /run/podman/podman.sock
LAN port:             17810
Container port:       7810
Shared network:       media-net
Public URL:           https://manage.roguegaming.com.au
Discovery depth:      4
Discovery cache:      10 seconds
```

The installer derives the Podman socket from the user who runs it; UID 1000 is only the default example.

## Install

Run as the user that owns the containers, not root:

```bash
cd /tmp
curl -fsSLO https://raw.githubusercontent.com/RogueAssassin/RogueForge/main/install.sh
chmod +x install.sh
./install.sh --engine podman
```

## Update

`update.sh` is the supported update path.

Latest release:

```bash
cd /opt/media-server/rogueforge
./update.sh latest
```

Pinned release:

```bash
./update.sh 0.8.3
```

If an older installation does not have the newest updater yet, bootstrap it once:

```bash
cd /opt/media-server/rogueforge
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/main/update.sh -o update.sh
chmod +x update.sh
./update.sh latest
```

The updater preserves `.env` and `data/auth.json`, stores deployment snapshots outside the stack scan tree under `/tmp/rogueforge-update-backups` (or `$TMPDIR/rogueforge-update-backups`), migrates older `data/update-backups` content there, updates the image, recreates RogueForge, and verifies `/health`.

## GHCR tags

Each version is published with convenient aliases:

```text
latest
0.8.3
v0.8.3
083
sha-<commit>
```

`latest` tracks the current main release; semantic and compact tags make pinning/rollback easy.

## Administrator account

```bash
cd /opt/media-server/rogueforge
python3 setup-auth.py --username administrator
podman-compose restart rogueforge
```

## Branding and service icons

RogueForge includes only its approved Base, Dark, and Light icon assets under `static/branding/`. Stack/service icons use Dashboard Icons with exact aliases and layered fallbacks. Nginx Proxy Manager resolves to `nginx-proxy-manager.svg`; Cloudflared resolves to `cloudflare.svg`.

## Operations drawer

The top bar now exposes an Operations activity drawer. Protected stack/container mutations are recorded locally in the browser with running/success/failure state, start time, duration and available command output. Completed history can be cleared without affecting workloads.

## Reverse proxy

For Nginx Proxy Manager, forward `https://manage.roguegaming.com.au` to `http://rogueforge:7810` on the shared `media-net`. Enable WebSockets and SSL. Live-log streaming sends `X-Accel-Buffering: no`.

## Documentation

- [Roadmap](MILESTONES.md)
- [Installation and reverse proxy](docs/INSTALL.md)
- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
- [GHCR publishing](docs/GHCR.md)
- [Security model](SECURITY.md)
- [Release history](CHANGELOG.md)

## Acknowledgements

Dockge and Uptime Kuma are product inspirations. RogueForge is an original implementation and does not copy their source code or branding.
