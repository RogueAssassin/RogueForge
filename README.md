![RogueForge](static/branding/rogueforge.svg)

# RogueForge

**A local-first operations console for Docker and Podman Compose.**

## Current testing release: 0.8.5

RogueForge 0.8.5 is the runtime-reliability release. It fixes Podman service updates, CPU/RAM statistics parsing, duplicate stack discovery, backup isolation, Nginx Proxy Manager/Cloudflared icon identity, and Runtime layout consistency. It is validated first through the `v0.8.5-runtime-fixes` testing channel before promotion to `main`.

### What it manages

- Recursive Compose discovery with active runtime labels taking precedence over filesystem candidates.
- Docker and rootless Podman through a mounted Unix socket.
- Stack Start, Stop, Restart, Pull, Recreate and Update.
- Compose and `.env` editing with backups stored outside the stacks tree.
- Container Start, Stop, Restart, Update, Recreate, Remove, Inspect, image checks, bulk actions and resource statistics.
- Live logs and authenticated terminal sessions.
- RogueForge self-protection, signed sessions, CSRF protection and login throttling.
- Dashboard Icons integration with explicit Nginx Proxy Manager and Cloudflared aliases.
- Operations history and stack health filtering.

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

Pinned production release:

```bash
./update.sh 0.8.4
```

## Test v0.8.5 before promotion

```bash
cd /opt/media-server/rogueforge
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/v0.8.5-runtime-fixes/update.sh -o update-testing.sh
chmod +x update-testing.sh
./update-testing.sh testing
```

Rollback at any time with `./update.sh 0.8.4`.

Update/editor backups are stored outside `/opt/media-server` under `/tmp/rogueforge/`, preventing RogueForge-created snapshots from being discovered as stacks.

## Planned production GHCR tags

```text
latest
0.8.5
v0.8.5
085
sha-<commit>
```

Testing builds publish `testing`, `branch-v0.8.5-runtime-fixes`, and a SHA tag without changing production aliases.

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
