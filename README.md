![RogueForge](docs/assets/rogueforge-banner.png)

# RogueForge

**A secure, local-first command centre for Docker and Podman Compose stacks.**

RogueForge discovers existing Compose projects and containers, shows runtime state, reads logs, edits Compose files with validation/backup, and performs authenticated lifecycle operations through the host container engine.

## Current release: 0.5.0

0.5.0 fixes the rootless Podman/Compose control path and deployment lifecycle. Podman container and Compose operations now target the mounted host socket consistently, RogueForge protects its own stack from in-app lifecycle actions, Restart no longer performs `down` followed by `up`, and upgrades now refresh the deployment bundle as well as the application image.

## Features

- Discover existing Docker or rootless Podman containers through the mounted Unix socket.
- Discover normal Compose files under the configured stacks directory without importing them into a proprietary database.
- Start, stop, restart, pull and recreate Compose projects.
- Restart individual containers and inspect their logs.
- Edit Compose files with automatic backup and validation before changes are accepted.
- Protect privileged operations with signed administrator sessions and CSRF validation.
- Keep RogueForge's own Compose project visible but protected from self-stop/restart/recreate operations.
- Reuse local service icons.
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

## First installation

Requirements:

- Linux with rootless Podman or Docker.
- `podman-compose` for Podman, or Docker Compose for Docker.
- Python 3, `curl`, Git and `sudo`.
- Run the installer as the user that owns the containers, not as root.

For 0.5.0:

```bash
cd /tmp
git clone --branch v0.5.0 --depth 1 \
  https://github.com/RogueAssassin/RogueForge.git rogueforge-install-0.5.0
cd rogueforge-install-0.5.0
chmod +x install.sh
./install.sh --engine podman
```

The installer:

1. Verifies the selected engine and Compose client.
2. Enables the current user's rootless Podman socket when Podman is selected.
3. Pulls the target image before changing the host deployment.
4. Creates `/opt/media-server/rogueforge` and persistent `data/` state.
5. Writes a host-specific `.env`, including the real current UID socket path.
6. Provisions the administrator account interactively.
7. Creates/reuses `media-net`.
8. Validates Compose before startup.
9. Starts RogueForge and waits for `/health`.

## Existing 0.4.x installation: upgrade to 0.5.0

Older 0.4.x `upgrade.sh` files only update the image, so perform this one-time bootstrap of the new upgrader and Compose definition:

```bash
cd /tmp
git clone --branch v0.5.0 --depth 1 \
  https://github.com/RogueAssassin/RogueForge.git rogueforge-upgrade-0.5.0

sudo cp -a /opt/media-server/rogueforge/compose.yaml \
  /opt/media-server/rogueforge/compose.yaml.pre-0.5.0
sudo cp -a /opt/media-server/rogueforge/.env \
  /opt/media-server/rogueforge/.env.pre-0.5.0
sudo cp -a /opt/media-server/rogueforge/data/auth.json \
  /opt/media-server/rogueforge/data/auth.json.pre-0.5.0

sudo install -m 0644 rogueforge-upgrade-0.5.0/compose.yaml \
  /opt/media-server/rogueforge/compose.yaml
sudo install -m 0755 rogueforge-upgrade-0.5.0/upgrade.sh \
  /opt/media-server/rogueforge/upgrade.sh
sudo chown -R "$(id -u):$(id -g)" /opt/media-server/rogueforge

cd /opt/media-server/rogueforge
./upgrade.sh 0.5.0
```

The 0.5.0 upgrader preserves `.env` and `data/auth.json`, backs up the deployment, pulls first, downloads the matching release deployment files, validates Compose, recreates RogueForge and verifies health.

## Normal future upgrades

```bash
cd /opt/media-server/rogueforge
./upgrade.sh 0.5.1
```

Or deliberately follow `main`/`latest`:

```bash
./upgrade.sh latest
```

## Login and password recovery

The default username is `administrator`.

Reset the password and invalidate existing sessions with:

```bash
cd /opt/media-server/rogueforge
python3 setup-auth.py --username administrator
podman-compose restart
```

Authentication data remains in `data/auth.json`. RogueForge 0.5.0 also reports whether that file exists, is readable and contains a valid credential record when authentication is unavailable.

## Runtime diagnostics

After signing in:

```bash
curl -b '<session-cookie>' http://127.0.0.1:17810/api/diagnostics
```

The diagnostics endpoint reports the selected engine/socket, remote Podman CLI status, stack root, self-stack guard, icon path and authentication-file status. The normal UI remains the preferred way to interact with RogueForge.

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

## Manual lifecycle

From `/opt/media-server/rogueforge` on a Podman host:

```bash
podman-compose ps
podman-compose restart
podman-compose down
podman-compose up -d
podman-compose logs -f
```

Do not add `-v` to `down` unless persistent data removal is intentional.

## Publishing 0.5.0

The GHCR workflow verifies that a semantic release tag matches `rogueforge.VERSION`. After the 0.5.0 source is finalized on `main`, create and push `v0.5.0`. The workflow publishes `0.5.0`, `0.5`, `latest`, and a commit-SHA tag.

## Documentation

- [Installation and reverse proxy](docs/INSTALL.md)
- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
- [GHCR publishing](docs/GHCR.md)
- [Security model](SECURITY.md)
- [Release history](CHANGELOG.md)
- [Milestones](MILESTONES.md)

## Acknowledgements

Dockge and Uptime Kuma are product inspirations. RogueForge is an original implementation and does not copy their source code or branding.
