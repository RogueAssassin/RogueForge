# RogueForge on Podman and media-net

This is the recommended deployment when Nginx Proxy Manager is already running as a rootless Podman container on the external `media-net` network.

## Address model

RogueForge uses two different ports intentionally:

```text
Container/network address:  http://rogueforge:7810
Host/LAN address:           http://<server-ip>:17810
Public proxy address:       https://manage.roguegaming.com.au
```

Port `7810` remains internal to the RogueForge container. Port `17810` is the configurable host-side port and can be changed without changing the NPM upstream.

## 1. Stop the system service

The existing host service must release its old port:

```bash
sudo systemctl disable --now rogueforge
```

This does not remove the old installation, so it can be restored if needed.

## 2. Place the RogueForge stack

Run these commands as `administrator`:

```bash
mkdir -p /opt/media-server/rogueforge
cd /opt/media-server/rogueforge
```

Extract the RogueForge 0.4.0 package into this directory. The directory should contain:

```text
Containerfile
compose.yaml
rogueforge.py
setup-auth.py
static/
.env.example
```

Create the local configuration:

```bash
cp .env.example .env
```

Review `.env`:

```text
PODMAN_UID=1000
ROGUEFORGE_HOST_PORT=17810
ROGUEFORGE_VERSION=0.4.0
ROGUEFORGE_STACKS_DIR=/opt/media-server
ROGUEFORGE_ICONS_DIR=/opt/media-server/rogue-dashboard/app/static/icons
ROGUEFORGE_PUBLIC_URL=https://manage.roguegaming.com.au
```

Change `ROGUEFORGE_HOST_PORT` if `17810` is already occupied. The internal port stays `7810`.

## 3. Provision the administrator

RogueForge deliberately ships without default credentials:

```bash
python3 setup-auth.py --username administrator
```

Alternatively generate a strong password and display it once:

```bash
python3 setup-auth.py --username administrator --generate
```

Protect the resulting local file:

```bash
chmod 700 data
chmod 600 data/auth.json
```

## 4. Confirm media-net

Using the same `administrator` account that owns NPM:

```bash
podman network exists media-net || podman network create media-net
podman network inspect media-net
```

Both NPM and RogueForge must belong to this same rootless network context.

## 5. Pull and start RogueForge from GHCR

Do not use `sudo` for these commands:

```bash
cd /opt/media-server/rogueforge
podman pull ghcr.io/rogueassassin/rogueforge:0.4.0
podman-compose up -d
podman ps --filter name=rogueforge
podman logs rogueforge
```

Test local and LAN access:

```bash
curl http://127.0.0.1:17810/health
curl http://<server-LAN-IP>:17810/health
```

If the second request fails, allow TCP port `17810` from your LAN in the host firewall. Do not forward this port from the internet.

For local development before a GHCR release exists:

```bash
podman-compose -f compose.yaml -f compose.build.yaml up -d --build
```

## 6. Verify NPM service discovery

```bash
podman exec nginx-proxy-manager getent hosts rogueforge
```

It should return the RogueForge container address. You can also inspect membership:

```bash
podman network inspect media-net
```

## 7. Configure Nginx Proxy Manager

Use these Proxy Host values:

```text
Domain Names:           manage.roguegaming.com.au
Scheme:                 http
Forward Hostname/IP:    rogueforge
Forward Port:           7810
Block Common Exploits:  On
Websockets Support:     On
Cache Assets:           Off
```

Request a Let's Encrypt certificate and enable Force SSL and HTTP/2. RogueForge now protects privileged actions with its administrator account; an NPM Access List remains useful as defence in depth.

## Podman socket design

The Compose stack mounts the rootless owner's socket:

```text
/run/user/1000/podman/podman.sock → /run/podman/podman.sock
```

RogueForge uses the Podman remote client through that Unix socket. The socket is never exposed over TCP. The container also uses `label=disable`, which Podman recommends when accessing its API socket from inside a container.

## Local icons

RogueForge looks for `.svg`, `.png`, `.webp`, `.jpg`, and `.jpeg` files in `ROGUEFORGE_ICONS_DIR`. Filenames are matched to stack and container names after normalization.

Examples:

```text
nginx-proxy-manager.png  → nginx-proxy-manager
uptime-kuma.svg          → uptime-kuma
rogue-dashboard.webp     → rogue-dashboard
```

The default points at Rogue Dashboard's existing `/opt/media-server/rogue-dashboard/app/static/icons` directory. If a logo is unavailable, RogueForge renders a generated initial tile without contacting an external icon service.

If your Rogue Dashboard logo directory is different, change only this `.env` value and recreate RogueForge:

```bash
podman-compose up -d --force-recreate
```

## Updating

Update the version in `.env`, then pull and recreate:

```bash
cd /opt/media-server/rogueforge
podman-compose pull
podman-compose up -d
```

## Rollback to the system service

```bash
cd /opt/media-server/rogueforge
podman-compose down
sudo systemctl enable --now rogueforge
```
