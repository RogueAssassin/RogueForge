# RogueForge 0.4.2 installation and proxy guide

## Resulting server layout

The default first installation creates:

```text
/opt/media-server/
├── rogueforge/
│   ├── compose.yaml
│   ├── setup-auth.py
│   ├── .env
│   └── data/
│       └── auth.json
├── rogue-dashboard/
│   └── app/static/icons/
└── <other Compose stacks>/
```

Application code remains inside the GHCR image. Only deployment configuration and persistent account data are stored on the host.

## Rootless Podman prerequisites

Run these as the user that owns the containers:

```bash
whoami
id -u
podman ps -a
podman info --format '{{.Host.Security.Rootless}}'
systemctl --user enable --now podman.socket
```

Do not run RogueForge’s installer with `sudo`. It invokes `sudo` only when `/opt` directories must be created or assigned to the current user.

## First installation

```bash
cd /tmp
git clone https://github.com/RogueAssassin/RogueForge.git rogueforge-install
cd rogueforge-install
git checkout v0.4.2
chmod +x install.sh
./install.sh
```

The GHCR image is pulled before the installer changes the server. An unavailable or private image therefore leaves the host untouched.

To override the defaults:

```bash
./install.sh \
  --install-dir /opt/media-server/rogueforge \
  --stacks-dir /opt/media-server \
  --icons-dir /opt/media-server/rogue-dashboard/app/static/icons \
  --image ghcr.io/rogueassassin/rogueforge:0.4.2 \
  --host-port 17810 \
  --network media-net \
  --public-url https://manage.roguegaming.com.au \
  --username administrator
```

## Verification

```bash
cd /opt/media-server/rogueforge
podman-compose ps
podman logs rogueforge
curl http://127.0.0.1:17810/health
podman network inspect media-net
podman exec nginx-proxy-manager getent hosts rogueforge
```

## Nginx Proxy Manager

Create a Proxy Host with:

```text
Domain Names:          manage.roguegaming.com.au
Scheme:                http
Forward Hostname/IP:   rogueforge
Forward Port:          7810
Cache Assets:          Off
Block Common Exploits: On
WebSockets Support:    On
```

Request a certificate, enable Force SSL, and enable HTTP/2. Only ports 80 and 443 should be forwarded from the internet. Keep host port `17810` private to the LAN.

## Troubleshooting an empty container list

Compare rootless and rootful stores:

```bash
podman ps -a
sudo podman ps -a
```

The normal installation must be run by the account for which the first command shows the expected containers. The container mounts `/run/user/<UID>/podman/podman.sock` for that user.

Check the socket:

```bash
uid=$(id -u)
ls -l "/run/user/$uid/podman/podman.sock"
curl --unix-socket "/run/user/$uid/podman/podman.sock" http://localhost/version
```

## Removal

This removes the RogueForge container while retaining the deployment and account data:

```bash
cd /opt/media-server/rogueforge
podman-compose down
```

Delete `/opt/media-server/rogueforge` only when you intentionally want to remove the administrator account and all local RogueForge configuration.
