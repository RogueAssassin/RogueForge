# RogueForge on rootless Podman and media-net

RogueForge 0.4.1 is distributed as a prebuilt GHCR image and installed with a small host-side deployment bundle.

## Why an installer is still needed

`podman pull` downloads the application image into Podman’s image store. OCI pulls do not create host directories, `.env`, Compose files, credentials, networks, or bind-mounted persistent data. `install.sh` performs those host-specific operations and then starts the pulled image.

## Default address model

```text
Container/network: http://rogueforge:7810
Host/LAN:          http://<server-ip>:17810
Public proxy:      https://manage.roguegaming.com.au
```

Nginx Proxy Manager and RogueForge share the external `media-net` network. NPM targets container port `7810`; the configurable host port is for LAN diagnostics and direct trusted access.

## Automated first installation

```bash
git clone https://github.com/RogueAssassin/RogueForge.git
cd RogueForge
git checkout v0.4.1
chmod +x install.sh
./install.sh
```

Run as the rootless Podman owner. The installer:

1. Validates requirements and paths.
2. Pulls `ghcr.io/rogueassassin/rogueforge:0.4.1` before host changes.
3. Refuses to overwrite an existing deployment.
4. Creates `/opt/media-server/rogueforge` and protected persistent data.
5. Writes the rootless user ID and requested settings to `.env`.
6. Provisions the first administrator interactively.
7. Creates or reuses `media-net`.
8. Starts the stack and waits for a successful health check.

## Compose mounts

```text
/run/user/<UID>/podman/podman.sock -> /run/podman/podman.sock
/opt/media-server                 -> /opt/media-server
./data                            -> /opt/rogueforge/data
```

The Podman socket remains a local Unix socket and is never exposed over TCP. The container uses `label=disable` to permit the explicitly configured bind mounts in common SELinux environments.

## Local icons

The default icon folder is:

```text
/opt/media-server/rogue-dashboard/app/static/icons
```

RogueForge recognizes SVG, PNG, WebP, JPG, and JPEG assets. Unknown services receive a generated initials tile and do not contact an external icon provider.

## Manual lifecycle

```bash
cd /opt/media-server/rogueforge
podman-compose pull
podman-compose up -d
podman-compose logs -f
podman-compose down
```

Do not use `sudo podman` for a rootless installation. That selects a different container store and socket.
