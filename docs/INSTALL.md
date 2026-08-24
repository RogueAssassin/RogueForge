# RogueForge 0.5.0 installation and proxy guide

## Default production layout

```text
/opt/media-server/
├── rogueforge/
│   ├── compose.yaml
│   ├── setup-auth.py
│   ├── upgrade.sh
│   ├── .env
│   └── data/
│       └── auth.json
├── rogue-dashboard/
│   └── app/static/icons/
└── <other Compose stacks>/
```

For FEILSBEASTSERVER the expected rootless Podman owner is UID 1000, so the host socket is `/run/user/1000/podman/podman.sock`. The installer still derives the UID dynamically from the account that runs it.

## Rootless Podman prerequisites

Run as the user that owns the containers:

```bash
whoami
id -u
podman ps -a
podman info --format '{{.Host.Security.Rootless}}'
systemctl --user enable --now podman.socket
podman-compose version
```

Do not run `install.sh` with `sudo`. The installer only invokes `sudo` when it needs to create or assign the `/opt/media-server/rogueforge` host directory.

## First installation

```bash
cd /tmp
git clone --branch v0.5.0 --depth 1 \
  https://github.com/RogueAssassin/RogueForge.git rogueforge-install-0.5.0
cd rogueforge-install-0.5.0
chmod +x install.sh
./install.sh --engine podman
```

The default deployment uses:

```text
Install directory:     /opt/media-server/rogueforge
Stacks directory:      /opt/media-server
Host port:             17810
Container port:        7810
Shared network:        media-net
Public URL:            https://manage.roguegaming.com.au
Icon directory:        /opt/media-server/rogue-dashboard/app/static/icons
Self stack:            rogueforge
```

The installer pulls the image before making deployment changes, writes the actual rootless socket source into `.env`, provisions `administrator`, validates Compose, starts the service and waits for `/health`.

## One-time 0.4.x to 0.5.0 upgrade

0.4.x upgraders only replaced the image. Bootstrap the new deployment definition and upgrader once:

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

From 0.5.0 onward, `upgrade.sh` backs up the deployment and downloads the matching release `compose.yaml`, `setup-auth.py`, `.env.example`, and upgrader while keeping the existing host `.env` and `data/auth.json`.

## Verification

```bash
cd /opt/media-server/rogueforge
podman-compose config
podman-compose ps
podman logs rogueforge
curl http://127.0.0.1:17810/health
podman network inspect media-net
podman exec nginx-proxy-manager getent hosts rogueforge
```

The health response should include `"ok":true` and version `0.5.0`.

## Podman socket verification

```bash
uid=$(id -u)
ls -l "/run/user/$uid/podman/podman.sock"
curl --unix-socket "/run/user/$uid/podman/podman.sock" http://localhost/version
```

RogueForge mounts this host socket at `/run/podman/podman.sock` inside its own container. Container operations use explicit remote Podman commands, while Compose commands receive `CONTAINER_HOST=unix:///run/podman/podman.sock` so they use the same host engine.

## Authentication troubleshooting

The default account name is `administrator`.

```bash
cd /opt/media-server/rogueforge
ls -l data/auth.json
python3 -m json.tool data/auth.json >/dev/null
python3 setup-auth.py --username administrator
podman-compose restart
```

RogueForge 0.5.0 reports missing/unreadable/invalid authentication state instead of only returning a generic login failure.

## Nginx Proxy Manager

```text
Domain Names:          manage.roguegaming.com.au
Scheme:                http
Forward Hostname/IP:   rogueforge
Forward Port:          7810
Cache Assets:          Off
Block Common Exploits: On
WebSockets Support:    On
```

Request a certificate, enable Force SSL and HTTP/2. NPM and RogueForge must both be connected to `media-net`.

## Manual lifecycle

```bash
cd /opt/media-server/rogueforge
podman-compose restart
podman-compose down
podman-compose up -d
podman-compose logs -f
```

The in-app RogueForge stack itself is intentionally protected from lifecycle and Compose editing operations. Manage RogueForge from the host deployment directory instead.
