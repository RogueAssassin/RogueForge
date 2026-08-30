<div align="center">

<table>
  <tr>
    <td width="220" align="center">
      <img src="https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/static/branding/rogueforge.svg" width="128" height="128" alt="RogueForge logo">
    </td>
    <td align="left">
      <h1>RogueForge</h1>
      <p><strong>Fast, local-first Docker and Podman stack operations.</strong></p>
      <p>Compose stacks • Verified updates • Live operations • Runtime resources • Local authentication</p>
    </td>
  </tr>
</table>

[![Testing](https://img.shields.io/badge/TESTING-0.9.1-8b5cf6?style=for-the-badge&labelColor=45464d)](https://github.com/RogueAssassin/RogueForge/tree/testing)
[![GHCR](https://img.shields.io/badge/GHCR-PACKAGE-5c6ac4?style=for-the-badge&logo=github&logoColor=white&labelColor=45464d)](https://github.com/RogueAssassin/RogueForge/pkgs/container/rogueforge)
[![Build](https://img.shields.io/github/actions/workflow/status/RogueAssassin/RogueForge/container.yml?branch=testing&style=for-the-badge&label=BUILD&labelColor=45464d)](https://github.com/RogueAssassin/RogueForge/actions/workflows/container.yml?query=branch%3Atesting)
![Runtime](https://img.shields.io/badge/RUNTIME-PYTHON%203.11-ff4fc8?style=for-the-badge&labelColor=45464d)
![Engine](https://img.shields.io/badge/ENGINE-DOCKER%20%7C%20PODMAN-00cbe6?style=for-the-badge&labelColor=45464d)
![Platform](https://img.shields.io/badge/PLATFORM-AMD64%20%7C%20ARM64-42d6a4?style=for-the-badge&labelColor=45464d)

</div>

RogueForge is a local-first operations console for self-hosted Docker and Podman environments. It discovers Compose projects, manages stack and container lifecycle, provides verified image updates, live logs, terminal access, configuration editing and lightweight runtime visibility from one authenticated interface.

RogueForge is designed to complement **[RogueDashboard](https://github.com/RogueAssassin/RogueDashboard)**. Use RogueForge for management and maintenance; use RogueDashboard for fast day-to-day service visibility, health, latency and application widgets.

## What RogueForge does

- Discovers Compose stacks recursively, preferring active runtime labels over duplicate filesystem candidates.
- Supports Docker and rootless Podman through a mounted Unix socket.
- Starts, stops, restarts, recreates, pulls and updates Compose stacks with deterministic lifecycle operations.
- Verifies replacement/update image identity instead of treating a successful pull as a successful deployment.
- Edits Compose and `.env` files with validation and backups outside the discovery tree.
- Manages individual containers with lifecycle, inspect, logs, terminal, update checks and resource statistics.
- Uses unified dashboard snapshots, short-lived inventory caching and asynchronous CPU/RAM refresh for a responsive UI.
- Provides signed sessions, CSRF protection, login throttling and RogueForge self-protection.
- Resolves service artwork through Dashboard Icons with explicit Nginx Proxy Manager and Cloudflared aliases.
- Records operation output and status for troubleshooting.

## Rogue ecosystem

### RogueForge

Full Docker/Podman Compose-stack and container management, verified lifecycle operations, configuration editing and runtime troubleshooting.

### RogueDashboard

For fast service visibility, health monitoring, latency and application widgets without giving the dashboard container-engine control:

**[Download / view RogueDashboard on GitHub](https://github.com/RogueAssassin/RogueDashboard)**

Both applications can share the same `media-net` network. RogueDashboard can read RogueForge's lightweight status APIs without receiving RogueForge administrator credentials or direct Docker/Podman engine access.

## Container images

Production:

```text
ghcr.io/rogueassassin/rogueforge:latest
```

Testing:

```text
ghcr.io/rogueassassin/rogueforge:testing
```

The repository uses two persistent branches: `main` is production-only and `testing` is active development. Testing publishes only `:testing` and immutable SHA tags; production publishes `:latest`, semantic version aliases and the immutable release tag.

## Path configuration

RogueForge separates the mounted host root from Compose discovery and `.env` locations:

```env
ROGUEFORGE_MEDIA_ROOT=/opt/media-server
ROGUEFORGE_COMPOSE_ROOT=/opt/media-server/compose
ROGUEFORGE_ENV_ROOT=/opt/media-server/compose
ROGUEFORGE_STACKS_DIR=/opt/media-server/compose
```

A stack such as `/opt/media-server/compose/dozzle/compose.yaml` with `/opt/media-server/compose/dozzle/.env` is supported directly. Administrators who keep stacks directly below `/opt/media-server` can point all roots there. `ROGUEFORGE_STACKS_DIR` remains a compatibility alias.

## Performance configuration

```env
ROGUEFORGE_DISCOVERY_CACHE=10
ROGUEFORGE_INVENTORY_CACHE=2
```

Overview, Stacks and Runtime share short-lived engine inventory. The browser can hydrate from its last session snapshot while fresh state loads in the background, and CPU/RAM statistics refresh independently so they do not block initial rendering.

## Install / update

Production update:

```bash
cd /opt/media-server/rogueforge
./update.sh latest
```

Testing channel:

```bash
cd /opt/media-server/rogueforge
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/update.sh -o update.sh
chmod +x update.sh
./update.sh testing
```

Update/editor backups are kept outside the stack discovery tree under `/tmp/rogueforge/`.

## 0.9.1 testing milestone

0.9.1 carries the validated 0.9.0 runtime-resource baseline forward and focuses on safety, recovery, observability and production hardening:

- incremental output streaming for long-running Pull/Update/Recreate operations,
- safe cancellation where the underlying operation supports it,
- persistent server-side operation/audit history,
- stack create/import/clone workflows,
- Compose templates and rollback UX,
- preservation of immediate targeted UI refresh after stack operations,
- operation timeouts and clearer recovery/failure reporting.

The permanent `testing` branch remains the proving ground. Changes are promoted to `main` only after regression testing.

## Road to production stability

Before the 1.0 single-host release, RogueForge will focus on:

1. **Operation safety** — transactional configuration saves, verified update/rollback paths, bounded subprocesses and recovery reporting.
2. **Engine efficiency** — shared inventory snapshots, targeted cache invalidation, no blocking CPU/RAM collection and reduced inspect/stats calls.
3. **Runtime resources** — image, volume and network inventory with guarded destructive operations and useful storage visibility.
4. **Auditability** — persistent operation history with actor, target, command class, result and duration.
5. **Compatibility testing** — automated Docker and rootless Podman lifecycle/update regression coverage.
6. **Upgrade guarantees** — documented backup, migration, rollback and health verification contracts.
7. **Security hardening** — permissions, rate limiting, reverse-proxy guidance and safe terminal/log handling.

See [MILESTONES.md](MILESTONES.md) for the tracked roadmap.

## Repository layout

```text
rogueforge.py          # single application runtime
VERSION                # canonical release metadata
setup-auth.py          # administrator password maintenance
install.sh             # first installation
update.sh              # production/testing updater
compose.yaml           # deployment
Containerfile          # image build
static/                # canonical web interface and branding
tests/                 # regression tests
rogueforge.py          # canonical application runtime (built directly; no source patch pipeline)
docs/                  # deployment documentation
```

The frontend is intentionally kept version-agnostic: active UI code lives in the canonical `app.js` / `styles.css` assets rather than release-specific compatibility files.

## Documentation

- [Roadmap](MILESTONES.md)
- [Installation](docs/INSTALL.md)
- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
- [GHCR publishing](docs/GHCR.md)
- [Security](SECURITY.md)
- [Release history](CHANGELOG.md)

## Acknowledgements

Dockge and Uptime Kuma are product inspirations. RogueForge is an original implementation and does not copy their source code or branding.
