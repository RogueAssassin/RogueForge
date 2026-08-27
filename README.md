![RogueForge](static/branding/rogueforge.svg)

# RogueForge

**A local-first operations console for Docker and Podman Compose.**

## Current testing release: 0.8.8

RogueForge 0.8.8 is the next Operations quality testing milestone. It builds on the validated 0.8.7 dashboard/performance baseline and now focuses on long-running operation visibility, safer cancellation where supported, stack create/import/clone workflows, Compose templates and rollback UX, and persistent server-side operation/audit history.

### What it manages

- Recursive Compose discovery with active runtime labels taking precedence over filesystem candidates.
- Docker and rootless Podman through a mounted Unix socket.
- Stack Start, Stop, Restart, Pull, Recreate and Update using deterministic Compose lifecycle operations.
- Compose and `.env` editing with backups stored outside the stacks tree.
- Container Start, Stop, Restart, verified Update, Recreate, Remove, Inspect, image checks, bulk actions and resource statistics.
- Fast unified dashboard snapshots plus short shared Podman inventory caching.
- Live logs and authenticated terminal sessions.
- RogueForge self-protection, signed sessions, CSRF protection and login throttling.
- Dashboard Icons integration with explicit Nginx Proxy Manager and Cloudflared aliases.
- Operations history and stack health filtering.

## Path configuration

RogueForge separates the host mount root from the locations used to discover Compose files and `.env` files:

```env
ROGUEFORGE_MEDIA_ROOT=/opt/media-server
ROGUEFORGE_COMPOSE_ROOT=/opt/media-server/compose
ROGUEFORGE_ENV_ROOT=/opt/media-server/compose
```

A layout such as `/opt/media-server/compose/dozzle/compose.yaml` and `/opt/media-server/compose/dozzle/.env` is supported directly. Administrators who store stacks directly below `/opt/media-server` can set all three roots to `/opt/media-server`.

`ROGUEFORGE_ENV_ROOT` uses the same relative stack layout as `ROGUEFORGE_COMPOSE_ROOT`. `ROGUEFORGE_STACKS_DIR` remains a compatibility alias and is synchronized to `ROGUEFORGE_COMPOSE_ROOT` by the updater.

## Performance configuration

```env
ROGUEFORGE_DISCOVERY_CACHE=10
ROGUEFORGE_INVENTORY_CACHE=2
```

The inventory cache avoids repeated Podman inventory calls while Overview, Stacks and Runtime are being rendered. The browser also keeps a short-lived session snapshot so returning to or refreshing RogueForge can display the last known dashboard immediately while fresh state is loaded in the background. CPU/RAM statistics remain a separate asynchronous refresh and do not block initial dashboard rendering.

## Production update

```bash
cd /opt/media-server/rogueforge
./update.sh latest
```

## Testing channel

```bash
cd /opt/media-server/rogueforge
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/update.sh -o update.sh
chmod +x update.sh
./update.sh testing
```

Update/editor backups are stored outside `/opt/media-server` under `/tmp/rogueforge/`.

## Planned production GHCR tags

```text
latest
0.8.8
v0.8.8
088
sha-<commit>
```

RogueForge uses two persistent branches: `main` for production and `testing` for active development. Testing builds publish `testing` and a SHA tag only; they never update `latest`, semantic version tags, or production release tags.

## Repository layout

```text
rogueforge.py          # single application runtime
VERSION                # canonical release metadata
setup-auth.py          # administrator password maintenance
install.sh             # first installation
update.sh              # production/testing updater
compose.yaml           # deployment
Containerfile          # image build
static/                # web interface and branding
tests/                 # regression tests
tools/                 # build-time release preparation
docs/                  # deployment documentation
```

## Documentation

- [Roadmap](MILESTONES.md)
- [Installation](docs/INSTALL.md)
- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
- [GHCR publishing](docs/GHCR.md)
- [Security](SECURITY.md)
- [Release history](CHANGELOG.md)

## Acknowledgements

Dockge and Uptime Kuma are product inspirations. RogueForge is an original implementation and does not copy their source code or branding.
