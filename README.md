# RogueForge 0.1.0

RogueForge is a Docker + Podman stack manager designed as the management companion to Rogue Dashboard.

The visual system intentionally mirrors Rogue Dashboard: midnight surfaces, violet primary accent, cyan secondary accent, neon-grid background, glass cards, rounded controls and the same typography hierarchy.

## MVP features

- Auto-detect Docker or Podman through the engine API socket.
- Native Podman socket support (`/run/podman/podman.sock`).
- Docker socket support (`/var/run/docker.sock`).
- Discover stack folders under `/opt/media-server`.
- Understand `podman-compose.yaml`, `compose.podman.yaml`, `docker-compose.yaml`, `docker-compose.yml`, `compose.yaml`, and `compose.yml`.
- Start / stop / restart / pull stacks.
- List all containers.
- Start / stop / restart containers.
- Read recent container logs.
- Edit compose YAML with automatic backup and `compose config` validation before save.
- 15-second live dashboard refresh.
- Headless systemd service.
- Bind to localhost by default so Nginx Proxy Manager/Cloudflare can publish it safely.

## Install on the WSL host

```bash
cd /tmp/RogueForge-0.1.0
sudo ./install.sh
```

Check:

```bash
systemctl status rogueforge --no-pager
curl http://127.0.0.1:7810/api/status
```

For your current rootful Podman server, set `/etc/default/rogueforge`:

```text
ROGUEFORGE_ENGINE=podman
ROGUEFORGE_SOCKET=/run/podman/podman.sock
```

Then:

```bash
sudo systemctl restart rogueforge
```

## Security

0.1.0 is intended for trusted LAN / reverse-proxy use. It binds to `127.0.0.1` by default. Do not expose it directly to the public Internet.

A later release should add Rogue Dashboard-compatible authentication/session handling, role-based actions, an audit log, masked `.env` editing and WebSocket log streaming before public exposure.

## Roadmap toward Dockge-class coverage

- `.env` editor with secret masking.
- Create/clone/delete stacks.
- Image browser/prune/pull UI.
- Network and volume browser.
- Podman pods.
- Docker Compose project metadata.
- Interactive terminal/exec.
- Live WebSocket logs.
- Update planning and rollback snapshots.
- Multi-host agents.
- User roles, sessions and audit log.
- Rogue Dashboard single-sign-on/deep-link integration.
- Stack startup dependency/readiness policies.
