# RogueForge 0.4.0

**The self-hosted operations console for Compose stacks.**

Version 0.4 adds administrator authentication and GHCR distribution to the container-networking and local-icon foundation introduced in 0.3.

## Secure account setup

RogueForge has no default password. Before starting the container:

```bash
python3 setup-auth.py --username administrator
```

This writes a salted password hash to `data/auth.json`. See [`SECURITY.md`](SECURITY.md) for the security model.

## Recommended Podman deployment

For Nginx Proxy Manager running on `media-net`, deploy RogueForge as a container on that same external network:

```text
NPM upstream:  http://rogueforge:7810
LAN access:    http://<server-ip>:17810
Public URL:    https://manage.roguegaming.com.au
```

See [`docs/CONTAINER_DEPLOYMENT.md`](docs/CONTAINER_DEPLOYMENT.md) for the migration procedure.

The default image is:

```text
ghcr.io/rogueassassin/rogueforge:0.4.0
```

Release history and planned work are tracked in [`CHANGELOG.md`](CHANGELOG.md) and [`MILESTONES.md`](MILESTONES.md).

RogueForge brings Docker and Podman stack management into one focused interface. Its workflow is inspired by the clarity and immediacy of Dockge and Uptime Kuma while retaining an original RogueForge visual identity and a dependency-free server.

## What changed in 0.2

- New persistent operations-console layout with responsive navigation.
- Overview dashboard with stack, container, running, and attention metrics.
- Compose stack health based on containers carrying Compose project labels.
- Searchable stack workspace and container inventory.
- Safer confirmations for disruptive actions.
- Compose editor with validation, backup, and automatic restore on failure.
- Container logs and lifecycle controls.
- Docker and Podman socket auto-detection.
- Demo mode for evaluating the interface without an engine.
- Mobile, tablet, and desktop layouts.
- Clear extension points for monitoring and multi-host agents.
- Rootless Podman user/socket support with owner-context CLI inventory and controls.
- Podman native Libpod API fallback and Podman Compose label discovery.
- Reverse-proxy hostname configuration and deployment guide.

## Fixing an empty Podman inventory

If RogueForge reports a connected Podman engine but shows zero containers, it is usually connected to the rootful store while your containers belong to a rootless Linux user.

Stop the existing service before upgrading:

```bash
sudo systemctl stop rogueforge
```

As the user that owns the containers, verify they are visible and note the UID:

```bash
podman ps -a
id -u
```

Then reinstall RogueForge for that Podman user. Replace `rogue` with the actual Linux account:

```bash
sudo ./install.sh \
  --podman-user rogue \
  --stacks-dir /opt/media-server
```

The installer enables the user's Podman socket and lingering, selects `/run/user/<UID>/podman/podman.sock`, and runs Compose operations as that same user. This keeps container listing and stack actions in the same Podman storage context.

See [`docs/INSTALL.md`](docs/INSTALL.md) for diagnostics, upgrades, and Nginx Proxy Manager setup.

## Current capabilities

- Discover `compose.yaml`, `compose.yml`, `docker-compose.yml`, Docker-specific, and Podman-specific Compose files.
- Start, stop, restart, and pull Compose projects.
- Start, stop, and restart individual containers.
- Read the latest 250 container log lines.
- Edit Compose YAML safely using `compose config` validation.
- Keep Compose files on disk so normal CLI workflows remain fully compatible.
- Bind to localhost by default for reverse-proxy deployment.

## Install

RogueForge supports a Linux host with Python 3.10+ and either Docker Compose V2 or `podman-compose`.

RogueForge should be installed **outside** the directory containing your Compose stacks. The application reads and operates those stacks, but it is not itself one of them.

Recommended layout:

```text
/opt/rogueforge/          RogueForge application files
/opt/stacks/              Compose stack directories managed by RogueForge
/etc/default/rogueforge   Runtime configuration
```

Your previous `/opt/media-server` location can still be used as the stacks directory. RogueForge itself should remain somewhere separate, such as `/opt/rogueforge`.

### Standard installation

```bash
unzip RogueForge.zip
cd RogueForge
sudo ./install.sh
```

Then open `http://127.0.0.1:7810` locally or publish it through a trusted reverse proxy.

The standard command installs RogueForge into `/opt/rogueforge` and scans `/opt/stacks`.

### Guided installation

Use the guided installer to choose paths and runtime settings interactively:

```bash
sudo ./install.sh --interactive
```

The installer asks for:

- RogueForge application directory.
- Compose stacks directory.
- Listen address and port.
- Docker, Podman, or automatic engine selection.

### Custom stacks directory

To keep existing stacks in `/opt/media-server`:

```bash
sudo ./install.sh --stacks-dir /opt/media-server
```

This produces the following separation:

```text
/opt/rogueforge/          RogueForge application
/opt/media-server/        Existing Compose stacks
```

For a typical server using `/srv/compose`:

```bash
sudo ./install.sh --stacks-dir /srv/compose
```

### Custom application and stacks directories

Both locations can be selected independently:

```bash
sudo ./install.sh \
  --install-dir /srv/rogueforge \
  --stacks-dir /mnt/appdata/compose
```

Paths must be absolute, contain no whitespace, and must not be identical.

### Explicit Docker setup

```bash
sudo ./install.sh \
  --engine docker \
  --socket /var/run/docker.sock \
  --stacks-dir /srv/compose
```

### Explicit Podman setup

```bash
sudo ./install.sh \
  --engine podman \
  --socket /run/podman/podman.sock \
  --stacks-dir /srv/compose
```

### Custom listen address and port

Keep `127.0.0.1` when publishing through a reverse proxy. For a trusted LAN-only deployment:

```bash
sudo ./install.sh --bind 0.0.0.0 --port 7810
```

Do not expose this directly to the public internet while authentication is not yet available.

Check the service:

```bash
systemctl status rogueforge --no-pager
curl http://127.0.0.1:7810/health
```

## Configuration

Edit `/etc/default/rogueforge` and restart the service after changes.

```text
ROGUEFORGE_BIND=127.0.0.1
ROGUEFORGE_PORT=7810
ROGUEFORGE_STACKS_DIR=/opt/stacks
ROGUEFORGE_ENGINE=auto
```

For rootful Podman:

```text
ROGUEFORGE_ENGINE=podman
ROGUEFORGE_SOCKET=/run/podman/podman.sock
```

For Docker:

```text
ROGUEFORGE_ENGINE=docker
ROGUEFORGE_SOCKET=/var/run/docker.sock
```

Each stack must live directly beneath the configured stacks directory:

```text
<stacks-directory>/
├── immich/
│   └── compose.yaml
├── media/
│   └── docker-compose.yml
└── paperless/
    ├── compose.yaml
    └── .env
```

RogueForge recognizes `compose.yaml`, `compose.yml`, `docker-compose.yaml`, `docker-compose.yml`, `podman-compose.yaml`, and `compose.podman.yaml`.

### Changing paths after installation

The easiest and safest approach is to rerun the installer with the new paths:

```bash
sudo ./install.sh --install-dir /srv/rogueforge --stacks-dir /srv/compose
```

An existing environment file is backed up with a timestamp before being updated. The system service is regenerated, reloaded, and restarted automatically.

## Demo mode

Demo mode supplies simulated engine and container data while retaining real stack discovery from the configured stacks directory.

```bash
ROGUEFORGE_DEMO=true ROGUEFORGE_STACKS_DIR=/opt/stacks python3 rogueforge.py
```

Lifecycle operations return simulated success in this mode. Compose editing still validates against the local Compose CLI, so use a disposable stacks directory when demonstrating edits.

## Security model

Version 0.2 is intended for localhost, a trusted LAN, or a protected reverse proxy. Do not expose it directly to the public internet. Access to the Docker or Podman socket is equivalent to powerful host control.

The next security milestone includes authenticated sessions, role-based permissions, CSRF protection, secret masking, an audit log, and narrowly scoped remote agents.

## Product roadmap

### 0.3 — Operate

- Create, clone, archive, and restore stacks.
- Masked `.env` editor.
- Live action output and log streaming.
- Image update planning and rollback snapshots.
- Networks, volumes, images, and Podman pods.

### 0.4 — Observe

- HTTP, TCP, DNS, ping, certificate, and container checks.
- Per-service latency and uptime history.
- Notification providers and maintenance windows.
- Public and private status pages.
- Automatic monitor suggestions from Compose metadata.

### 0.5 — Scale

- Outbound-only RogueForge agents.
- Multi-host dashboards and host health.
- Authentication, 2FA, roles, and audit history.
- Git-backed stack delivery and approvals.
- Backup policies and scheduled operations.

## Design principles

1. **Compose files remain yours.** RogueForge never traps stack configuration in an internal-only database.
2. **Real-time feedback.** Operations should show useful progress and errors immediately.
3. **Safe by default.** Validate changes, preserve backups, and confirm disruptive actions.
4. **One calm interface.** Deployment and monitoring should feel like one coherent product.
5. **Agent-based remote access.** Do not expose unauthenticated Docker sockets over a network.

## License

Add your chosen license before publishing. Dockge and Uptime Kuma should be credited as product inspirations; RogueForge does not include their source code.
