![RogueForge](static/branding/rogueforge.svg)

# RogueForge

**A local-first operations console for Docker and Podman Compose.**

## Current testing release: 0.8.6

RogueForge 0.8.6 focuses on reliable Podman updates and configurable stack locations. It adds verified image replacement for Compose-managed Podman containers, separates the media mount root from Compose and `.env` roots, retains 0.8.5 CPU/RAM/discovery/UI fixes, and validates the branch before publishing the `testing` image.

### What it manages

- Recursive Compose discovery with active runtime labels taking precedence over filesystem candidates.
- Docker and rootless Podman through a mounted Unix socket.
- Stack Start, Stop, Restart, Pull, Recreate and Update.
- Compose and `.env` editing with backups stored outside the stacks tree.
- Container Start, Stop, Restart, verified Update, Recreate, Remove, Inspect, image checks, bulk actions and resource statistics.
- Live logs and authenticated terminal sessions.
- RogueForge self-protection, signed sessions, CSRF protection and login throttling.
- Dashboard Icons integration with explicit Nginx Proxy Manager and Cloudflared aliases.
- Operations history and stack health filtering.

## Path configuration

RogueForge 0.8.6 separates the host mount root from the locations used to discover Compose files and `.env` files:

```env
ROGUEFORGE_MEDIA_ROOT=/opt/media-server
ROGUEFORGE_COMPOSE_ROOT=/opt/media-server/compose
ROGUEFORGE_ENV_ROOT=/opt/media-server/compose
```

For FEILSBEASTSERVER, a stack such as Dozzle resolves as:

```text
/opt/media-server/compose/dozzle/compose.yaml
/opt/media-server/compose/dozzle/.env
```

If an administrator stores everything beneath one root, the settings can all be the same, for example:

```env
ROGUEFORGE_MEDIA_ROOT=/opt/media-server
ROGUEFORGE_COMPOSE_ROOT=/opt/media-server
ROGUEFORGE_ENV_ROOT=/opt/media-server
```

`ROGUEFORGE_ENV_ROOT` uses the same relative stack layout as `ROGUEFORGE_COMPOSE_ROOT`. `ROGUEFORGE_STACKS_DIR` remains a compatibility alias and is synchronized to `ROGUEFORGE_COMPOSE_ROOT` by the updater. Compose and env roots should live beneath the mounted media root.

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

## Production update

```bash
cd /opt/media-server/rogueforge
./update.sh latest
```

## Test v0.8.6 before promotion

```bash
cd /opt/media-server/rogueforge
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/v0.8.6-testing/update.sh -o update-testing.sh
chmod +x update-testing.sh
./update-testing.sh testing
```

Rollback to a known production release at any time, for example `./update.sh 0.8.4`.

Update/editor backups are stored outside `/opt/media-server` under `/tmp/rogueforge/`, preventing RogueForge-created snapshots from being discovered as stacks.

## Podman update verification

For a Compose-managed Podman service, RogueForge now pulls the requested image, compares immutable image IDs, preserves the old container under a temporary name, recreates the service from its authoritative Compose file, verifies the new running image ID, and removes the preserved container only after verification. If recreation fails, RogueForge attempts to restore and restart the previous container.

## Planned production GHCR tags

```text
latest
0.8.6
v0.8.6
086
sha-<commit>
```

Testing builds publish `testing`, `branch-v0.8.6-testing`, and a SHA tag without changing production aliases.

## Branding and service icons

RogueForge includes Base, Dark and Light branding under `static/branding/`. Service icon selection prioritizes container image/service identity so `jc21/nginx-proxy-manager` resolves to Nginx Proxy Manager and `cloudflare/cloudflared` resolves to Cloudflare regardless of the Compose project name.

## Documentation

- [Roadmap](MILESTONES.md)
- [Installation](docs/INSTALL.md)
- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
- [GHCR publishing](docs/GHCR.md)
- [Security](SECURITY.md)
- [Release history](CHANGELOG.md)

## Acknowledgements

Dockge and Uptime Kuma are product inspirations. RogueForge is an original implementation and does not copy their source code or branding.
