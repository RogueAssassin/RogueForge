# RogueForge on Docker, rootless Podman, and media-net

RogueForge 0.4.3 is distributed as a prebuilt GHCR image and installed with a small host-side deployment bundle.

## Why an installer is still needed

`podman pull` or `docker pull` downloads the application image into the engine’s image store. OCI pulls do not create host directories, `.env`, Compose files, credentials, networks, or bind-mounted persistent data. `install.sh` performs those host-specific operations and then starts the pulled image.

## Default address model

```text
Container/network: http://rogueforge:7810
Host/LAN:          http://<server-ip>:17810
Public proxy:      https://manage.roguegaming.com.au
```

Nginx Proxy Manager and RogueForge share the external `media-net` network. NPM targets container port `7810`; the configurable host port is for LAN diagnostics and direct trusted access.

## Automated first installation

```bash
git clone --branch v0.4.3 --depth 1 https://github.com/RogueAssassin/RogueForge.git RogueForge-0.4.3
cd RogueForge-0.4.3
chmod +x install.sh
./install.sh
```

Run as the user that owns the Docker or rootless Podman containers. The installer:

1. Validates requirements and paths.
2. Detects Docker or rootless Podman and pulls `ghcr.io/rogueassassin/rogueforge:0.4.3` before host changes.
3. Refuses to overwrite an existing deployment.
4. Creates `/opt/media-server/rogueforge` and protected persistent data.
5. Writes the selected engine and socket plus requested settings to `.env`.
6. Provisions the first administrator interactively.
7. Creates or reuses `media-net`.
8. Starts the stack and waits for a successful health check.

## Compose mounts

```text
/run/user/<UID>/podman/podman.sock -> /run/podman/podman.sock
/opt/media-server                 -> /opt/media-server
./data                            -> /opt/rogueforge/data
```

For Docker, `/var/run/docker.sock` is mounted at the same path instead. Both engine sockets remain local Unix sockets and are never exposed over TCP. The container uses `label=disable` to permit the explicitly configured bind mounts in common SELinux environments.

## Local icons

The default icon folder is:

```text
/opt/media-server/rogue-dashboard/app/static/icons
```

RogueForge recognizes SVG, PNG, WebP, JPG, and JPEG assets. Unknown services receive a generated initials tile and do not contact an external icon provider.

## Manual lifecycle

Podman:

```bash
cd /opt/media-server/rogueforge
podman-compose pull
podman-compose up -d
podman-compose logs -f
podman-compose down
```

Do not use `sudo podman` for a rootless installation. That selects a different container store and socket.

Docker:

```bash
cd /opt/media-server/rogueforge
docker compose pull
docker compose up -d
docker compose logs -f
docker compose down
```
