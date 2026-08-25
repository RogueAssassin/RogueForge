![RogueForge](static/branding/rogueforge.svg)

# RogueForge

**A local-first operations console for Docker and Podman Compose.**

## Current release: 0.8.4

RogueForge 0.8.4 advances the **Operations Quality** milestone with health-focused stack management, filterable/exportable Operations history, cleaner non-versioned frontend quality assets, and a corrected release workflow that stamps the actual published runtime with the root `VERSION` value.

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
- Centralized stack/service icons from Dashboard Icons, with jsDelivr, raw-GitHub, local and generic fallbacks.
- Persistent browser-side Operations history with status filtering, captured output and JSON export.
- Stack health filtering for healthy, partial and stopped workloads with stronger fault highlighting.

## Repository layout

```text
rogueforge.py          # complete application runtime
VERSION                # canonical release metadata
setup-auth.py          # administrator password maintenance
install.sh             # first installation
update.sh              # updates/releases
compose.yaml           # deployment
Containerfile          # image build
static/                # web interface, operations layer and branding
tests/                 # validation tests
docs/                  # deployment documentation
```

There are no versioned `rogueforge_v*.py` entry points and no backend runtime extension modules.

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

```bash
cd /opt/media-server/rogueforge
./update.sh latest
```

Pinned release:

```bash
./update.sh 0.8.4
```

If an older installation needs the newest updater first:

```bash
cd /opt/media-server/rogueforge
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/main/update.sh -o update.sh
chmod +x update.sh
./update.sh latest
```

The updater preserves `.env` and `data/auth.json`, stores deployment snapshots outside the stack scan tree under `/tmp/rogueforge-update-backups` (or `$TMPDIR/rogueforge-update-backups`), migrates older `data/update-backups` content there, recreates RogueForge, and verifies `/health`.

## GHCR tags

Each version is published as:

```text
latest
0.8.4
v0.8.4
084
sha-<commit>
```

The workflow stamps the runtime with the canonical `VERSION` immediately before both validation and the actual container build, so `/health`, the UI version and GHCR aliases refer to the same release.

## Administrator account

```bash
cd /opt/media-server/rogueforge
python3 setup-auth.py --username administrator
podman-compose restart rogueforge
```

## Branding and service icons

RogueForge includes its approved Base, Dark, and Light assets under `static/branding/`. Stack/service icons use Dashboard Icons with exact aliases and layered fallbacks. Nginx Proxy Manager resolves to `nginx-proxy-manager.svg`; Cloudflared resolves to `cloudflare.svg`.

## Operations and health

The top bar Operations drawer records protected stack/container mutations locally with running/success/failure state, timestamps, duration and command output. v0.8.4 adds status filters and JSON export. The Stacks view adds All/Healthy/Partial/Stopped filters and visual fault rails so degraded workloads stand out immediately.

## Reverse proxy

For Nginx Proxy Manager, forward the configured public hostname to `http://rogueforge:7810` on the shared `media-net`. Enable WebSockets and SSL. Live-log streaming sends `X-Accel-Buffering: no`.

## Documentation

- [Roadmap](MILESTONES.md)
- [Installation and reverse proxy](docs/INSTALL.md)
- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
- [GHCR publishing](docs/GHCR.md)
- [Security model](SECURITY.md)
- [Release history](CHANGELOG.md)

## Acknowledgements

Dockge and Uptime Kuma are product inspirations. RogueForge is an original implementation and does not copy their source code or branding.
