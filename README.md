![RogueForge](docs/assets/rogueforge-banner.png)

# RogueForge

**A secure, local-first command centre for Docker and Podman Compose stacks.**

RogueForge discovers existing stacks and containers, shows their state, reads logs, and performs authenticated lifecycle and Compose operations. Its workflow takes inspiration from the file-based clarity of Dockge and the approachable interface of Uptime Kuma while remaining an original implementation.

## Features

- Manage normal Compose files without importing them into a proprietary database.
- Discover Docker or rootless Podman containers through the local Unix socket.
- Start, stop, restart, pull, inspect logs, and safely edit Compose projects.
- Require administrator login for privileged operations.
- Connect directly to Nginx Proxy Manager over a shared network.
- Reuse local service icons without an external icon provider.
- Pull prebuilt `linux/amd64` and `linux/arm64` images from GHCR.
- Upgrade in place with preflight pulling, health verification, and rollback.

## How GHCR installation works

`docker pull` or `podman pull` downloads the application image into the engine’s image store. An OCI image cannot safely create `/opt/media-server/rogueforge`, `.env`, credentials, networks, or persistent bind-mounted folders on the host.

RogueForge therefore uses the same practical model as other Compose applications:

1. Keep a small Compose deployment in `/opt/media-server/rogueforge`.
2. Keep persistent account data in `/opt/media-server/rogueforge/data`.
3. Pull the application from `ghcr.io/rogueassassin/rogueforge`.
4. Start or update it using the host’s Compose command.

## First installation

### Requirements

- Linux with Docker Engine or rootless Podman.
- Docker Compose v2, `docker-compose`, or `podman-compose`.
- Python 3, `curl`, Git, and `sudo` for creating the `/opt` directory.
- Run the installer as the user that owns the containers—not as root.

### Automatic runtime detection

```bash
cd /tmp
git clone --branch v0.4.3 --depth 1 \
  https://github.com/RogueAssassin/RogueForge.git rogueforge-install-0.4.3
cd rogueforge-install-0.4.3
chmod +x install.sh
./install.sh
```

The installer pulls the image before changing the host, detects Podman or Docker, creates `/opt/media-server/rogueforge`, provisions the first administrator, creates or reuses `media-net`, starts the container, and waits for a healthy response.

Use a new clone directory for each release. This avoids checkout failures caused by local changes in an older installer checkout.

### Explicit rootless Podman installation

```bash
./install.sh --engine podman
```

This enables the current user’s Podman socket and mounts:

```text
/run/user/<UID>/podman/podman.sock -> /run/podman/podman.sock
```

Run normal lifecycle commands without `sudo`:

```bash
podman-compose ps
```

### Explicit Docker installation

The current user must already have permission to access `/var/run/docker.sock`:

```bash
docker info
./install.sh --engine docker
```

The deployment mounts:

```text
/var/run/docker.sock -> /var/run/docker.sock
```

RogueForge uses Docker’s API for inventory and container actions and the bundled Docker Compose client for stack operations.

### Custom paths and networking

```bash
./install.sh \
  --engine podman \
  --install-dir /opt/media-server/rogueforge \
  --stacks-dir /opt/media-server \
  --icons-dir /opt/media-server/rogue-dashboard/app/static/icons \
  --host-port 17810 \
  --network media-net \
  --public-url https://manage.roguegaming.com.au
```

## Open RogueForge

```text
LAN:          http://<server-ip>:17810
NPM upstream: http://rogueforge:7810
Public URL:   https://manage.roguegaming.com.au
```

The default account name is `administrator`; the password is created interactively during installation.

## Updating

Use the installed deployment directory, not the temporary Git checkout:

```bash
cd /opt/media-server/rogueforge
./upgrade.sh 0.4.3
```

For a future release, substitute its semantic version:

```bash
cd /opt/media-server/rogueforge
./upgrade.sh 0.4.4
```

To deliberately follow the mutable channel:

```bash
./upgrade.sh latest
```

The upgrader automatically uses the Docker or Podman runtime recorded during installation. It pulls first, backs up `.env`, recreates the container, verifies health, and restores the previous image if startup fails.

### One-time upgrade from v0.4.1 or v0.4.2

Older installations do not contain the final runtime-aware upgrader. Use a clean clone so no local checkout changes can block the operation:

```bash
cd /tmp
git clone --branch v0.4.3 --depth 1 \
  https://github.com/RogueAssassin/RogueForge.git rogueforge-upgrade-0.4.3
sudo cp -a /opt/media-server/rogueforge/compose.yaml \
  /opt/media-server/rogueforge/compose.yaml.pre-0.4.3
sudo install -m 0644 rogueforge-upgrade-0.4.3/compose.yaml \
  /opt/media-server/rogueforge/compose.yaml
sudo install -m 0755 rogueforge-upgrade-0.4.3/upgrade.sh \
  /opt/media-server/rogueforge/upgrade.sh
sudo chown -R "$(id -u):$(id -g)" /opt/media-server/rogueforge
cd /opt/media-server/rogueforge
./upgrade.sh 0.4.3
```

## Restart, stop, start, and logs

First navigate to the deployment:

```bash
cd /opt/media-server/rogueforge
```

Podman:

```bash
podman-compose restart
podman-compose down
podman-compose up -d
podman-compose logs -f
```

Docker:

```bash
docker compose restart
docker compose down
docker compose up -d
docker compose logs -f
```

These commands preserve `.env` and `data/auth.json`. Do not add `-v` to `down` unless persistent data removal is intentional.

## Login and password recovery

The username is `administrator`, not `admin`. Reset the password and invalidate existing sessions with:

```bash
cd /opt/media-server/rogueforge
python3 setup-auth.py --username administrator
```

Restart the container afterward using the command for your runtime.

## Nginx Proxy Manager

| Setting | Value |
| --- | --- |
| Domain | `manage.roguegaming.com.au` |
| Scheme | `http` |
| Forward hostname | `rogueforge` |
| Forward port | `7810` |
| WebSockets | enabled |
| Block Common Exploits | enabled |
| Force SSL | enabled after issuing the certificate |

NPM and RogueForge must belong to the same `${ROGUEFORGE_NETWORK:-media-net}` network.

## Publishing GHCR releases

Normal servers should use semantic tags such as:

```text
ghcr.io/rogueassassin/rogueforge:0.4.3
```

Push the source and matching release tag:

```bash
git add .
git commit -m "Release RogueForge v0.4.3"
git push origin main
git tag v0.4.3
git push origin v0.4.3
```

The workflow publishes `0.4.3`, `0.4`, `latest`, and `sha-<commit>` tags. It refuses a tag that does not match RogueForge’s internal application version.

## Documentation

- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
- [Installation and reverse proxy](docs/INSTALL.md)
- [GHCR publishing](docs/GHCR.md)
- [Security model](SECURITY.md)
- [Release history](CHANGELOG.md)
- [Milestones](MILESTONES.md)

## Acknowledgements

Dockge and Uptime Kuma are product inspirations. RogueForge is an original implementation and does not copy their source code or branding.
