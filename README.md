<div align="center">

<img src="https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/static/branding/rogueforge.svg" width="128" height="128" alt="RogueForge logo">

# RogueForge

**Local-first Docker and Podman stack management, verified updates and live troubleshooting.**

[![Release](https://img.shields.io/badge/RELEASE-1.5.0%20TESTING-8b5cf6?style=for-the-badge&labelColor=45464d)](https://github.com/RogueAssassin/RogueForge/tree/testing)
[![Build](https://img.shields.io/github/actions/workflow/status/RogueAssassin/RogueForge/container.yml?branch=testing&style=for-the-badge&label=BUILD&labelColor=45464d)](https://github.com/RogueAssassin/RogueForge/actions/workflows/container.yml?query=branch%3Atesting)
![Engine](https://img.shields.io/badge/ENGINE-DOCKER%20%7C%20PODMAN-00cbe6?style=for-the-badge&labelColor=45464d)
![Platform](https://img.shields.io/badge/PLATFORM-AMD64%20%7C%20ARM64-42d6a4?style=for-the-badge&labelColor=45464d)

</div>

RogueForge is the management and troubleshooting layer for the Rogue media-server stack. It discovers Compose projects, safely controls stacks and containers, performs verified image updates, streams logs on demand, provides authenticated terminal access, edits Compose/.env files transactionally and exposes lightweight runtime inventory.

RogueForge deliberately stays separate from **RogueDashboard**, which owns monitoring, uptime, incidents and notifications, and **RogueMediaValidator**, which owns torrent/media validation and protection.

## Highlights

- verified Start, Stop, Restart, Recreate and Update workflows
- per-stack lifecycle serialization to prevent competing actions
- in-place updates with immutable image verification and rollback
- bounded operation history with timeout, cancellation, progress and export
- on-demand live logs with search, severity filtering, pause/resume and download
- authenticated per-container terminal access
- Images, Volumes and Networks inventory
- transactional Compose and `.env` editing with validation and backup
- Docker and rootless Podman support
- short-lived inventory/dashboard caches and bounded engine concurrency
- canonical deployment under `/opt/media-server/rogueforge`
- no permanent log indexer and no high-frequency background engine polling

## 1.5.0 stack management and update intelligence

RogueForge 1.5.0 builds on the tested lifecycle and logging baseline with safer update visibility.

- added a pre-update stack preview showing affected running services and image references
- shows current running image IDs and locally tagged image IDs before confirmation
- highlights locally available image changes without performing a background pull
- keeps the actual update path as pull → in-place recreate → immutable image verification → rollback on failure
- preserves strict per-stack lifecycle serialization
- introduces the append-only environment revision convention beginning with `Rev 150 update`
- keeps `.env.example` as the complete fresh-install reference while upgrades preserve existing `.env`
- retains the 1.4 live-log filtering, reconnect visibility and bounded operation history

## Rogue ecosystem

| Service | Responsibility |
| --- | --- |
| **RogueDashboard** | visibility, health, uptime, incidents and alerts |
| **RogueForge** | container/stack management, updates, logs and terminal |
| **RogueMediaValidator** | torrent/media validation and protection |
| **RogueRoute GPX** | routing and GPX services |

RogueDashboard can consume RogueForge's lightweight status information without receiving Docker/Podman socket access or RogueForge administrator credentials.

## Default layout

```text
/opt/media-server/
├── rogueforge/
│   ├── compose.yaml
│   ├── .env
│   ├── update.sh
│   ├── setup-auth.py
│   └── data/
│       ├── auth.json
│       └── operations.json
├── radarr/
├── sonarr/
├── bazarr/
├── qbittorrent/
├── rogue-dashboard/
└── ...
```

RogueForge's own deployment stays in `/opt/media-server/rogueforge`. Stack discovery remains rooted at `/opt/media-server` so sibling Compose projects remain visible.

## Quick install — Podman

```bash
mkdir -p /opt/media-server/rogueforge
cd /opt/media-server/rogueforge

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/.env.example -o .env
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/setup-auth.py -o setup-auth.py
chmod 600 .env

# Set ROGUEFORGE_SOCKET_SOURCE to /run/user/$(id -u)/podman/podman.sock
nano .env
python3 setup-auth.py --username administrator

podman network inspect media-net >/dev/null 2>&1 || podman network create media-net
podman compose --env-file .env -f compose.yaml pull
podman compose --env-file .env -f compose.yaml up -d
```

Open:

```text
http://HOST:17810
```

## Quick install — Docker

```bash
mkdir -p /opt/media-server/rogueforge
cd /opt/media-server/rogueforge

curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/compose.yaml -o compose.yaml
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/.env.example -o .env
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/setup-auth.py -o setup-auth.py
chmod 600 .env
```

Set the Docker socket values documented in `.env`, create authentication, then start with:

```bash
docker network inspect media-net >/dev/null 2>&1 || docker network create media-net
docker compose --env-file .env -f compose.yaml pull
docker compose --env-file .env -f compose.yaml up -d
```

## Updating

Testing:

```bash
cd /opt/media-server/rogueforge
./update.sh testing
```

Pinned version:

```bash
./update.sh 1.5.0
```

Production after promotion:

```bash
./update.sh latest
```

The updater preserves the existing `.env` and persistent authentication/operation data.

## Performance defaults

```env
ROGUEFORGE_DISCOVERY_CACHE=10
ROGUEFORGE_INVENTORY_CACHE=2
ROGUEFORGE_DASHBOARD_CACHE=3
ROGUEFORGE_DASHBOARD_STALE=30
ROGUEFORGE_RESOURCE_CACHE=15
ROGUEFORGE_ENGINE_DETAIL_CONCURRENCY=4
ROGUEFORGE_MAX_LOG_STREAMS=6
ROGUEFORGE_LOG_TAIL=200
```

The supplied `.env.example` documents every deployment, lifecycle, performance, logging and terminal setting.

## Persistent files

Keep these between upgrades:

```text
.env
data/auth.json
data/operations.json
```

## Security model

RogueForge:

- requires local administrator authentication for protected operations
- uses signed sessions, CSRF protection and login throttling
- protects its own stack from in-app lifecycle actions
- limits terminal and live-log concurrency
- validates stack configuration before saving
- stores backups outside the Compose discovery tree
- requires intentional Docker/Podman socket access because engine management is its purpose

Keep RogueForge behind a trusted reverse proxy and do not expose the engine socket beyond the RogueForge container.

## Documentation

- [Installation](docs/INSTALL.md)
- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
- [GHCR publishing](docs/GHCR.md)
- [Security](SECURITY.md)
- [Roadmap](MILESTONES.md)
- [Changelog](CHANGELOG.md)

## Release channels

Testing:

```text
ghcr.io/rogueassassin/rogueforge:testing
```

Production after promotion:

```text
ghcr.io/rogueassassin/rogueforge:latest
ghcr.io/rogueassassin/rogueforge:1.5.0
```

The permanent `testing` branch is the proving ground. `main` remains production-only.
