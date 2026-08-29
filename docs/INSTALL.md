# RogueForge installation and upgrade guide

This guide describes the current RogueForge deployment model. The canonical version is stored in `VERSION`; `main` is production and `testing` is the development channel.

## Default layout

A typical media-server deployment uses:

```text
/opt/media-server/
├── rogueforge/
│   ├── compose.yaml
│   ├── update.sh
│   ├── setup-auth.py
│   ├── .env
│   └── data/
│       └── auth.json
└── compose/
    ├── bazarr/
    │   ├── compose.yaml
    │   └── .env
    ├── dozzle/
    │   ├── compose.yaml
    │   └── .env
    └── ...
```

The locations are configurable:

```env
ROGUEFORGE_MEDIA_ROOT=/opt/media-server
ROGUEFORGE_COMPOSE_ROOT=/opt/media-server/compose
ROGUEFORGE_ENV_ROOT=/opt/media-server/compose
ROGUEFORGE_STACKS_DIR=/opt/media-server/compose
```

If Compose projects live directly below `/opt/media-server`, point the Compose and environment roots there instead.

## Rootless Podman prerequisites

Run RogueForge as the same user that owns the containers:

```bash
whoami
id -u
podman version
podman ps -a
systemctl --user enable --now podman.socket
podman compose version
```

Do not run the deployment with `sudo podman`; that selects a different container store and socket.

The rootless socket is normally:

```text
/run/user/<UID>/podman/podman.sock
```

and is mounted into RogueForge as:

```text
/run/podman/podman.sock
```

## Production install

```bash
git clone --branch main --depth 1 https://github.com/RogueAssassin/RogueForge.git
cd RogueForge
chmod +x install.sh
./install.sh --engine podman
```

The installer validates the runtime and Compose provider, checks the configured roots, provisions the rootless socket mapping, creates authentication when needed, pulls the GHCR image, starts RogueForge and waits for `/health`.

## Testing install / switch

The permanent development channel is `testing`:

```bash
cd /opt/media-server/rogueforge
curl -fsSL https://raw.githubusercontent.com/RogueAssassin/RogueForge/testing/update.sh -o update.sh
chmod +x update.sh
./update.sh testing
```

Testing uses `ghcr.io/rogueassassin/rogueforge:testing` and never changes production tags.

## Updating

Production latest:

```bash
cd /opt/media-server/rogueforge
./update.sh latest
```

Pinned production version:

```bash
./update.sh X.Y.Z
```

Testing:

```bash
./update.sh testing
```

The updater backs up deployment files under `/tmp/rogueforge/update-backups/`, pulls the requested image, recreates RogueForge when the immutable image ID changed, verifies the new running image ID, and then verifies `/health`. It does not overwrite `.env` or `data/auth.json`.

## Verification

```bash
curl -fsS http://127.0.0.1:17810/health
podman ps --filter name=rogueforge
podman inspect rogueforge --format 'Image={{.Image}} ConfigImage={{.Config.Image}}'
podman exec rogueforge podman --remote --url unix:///run/podman/podman.sock info
```

## Authentication maintenance

There is no default password. Provision or replace the administrator credentials locally:

```bash
cd /opt/media-server/rogueforge
python3 setup-auth.py --username administrator
```

The persistent file is:

```text
/opt/media-server/rogueforge/data/auth.json
```

Re-provisioning invalidates existing sessions.

## Reverse proxy

A typical Nginx Proxy Manager target is:

```text
Scheme:           http
Forward hostname: rogueforge
Forward port:     7810
WebSockets:       enabled
Public URL:       https://manage.example.com
```

Set `ROGUEFORGE_PUBLIC_URL` to the HTTPS public URL so secure-session behaviour is correct. RogueForge and the proxy must share a container network such as `media-net`.

## Manual RogueForge lifecycle

RogueForge protects its own stack from in-app lifecycle actions. Manage the RogueForge container from its host deployment directory:

```bash
cd /opt/media-server/rogueforge
podman compose --env-file .env -f compose.yaml pull
podman compose --env-file .env -f compose.yaml up -d
podman logs -f rogueforge
```

For application-managed stacks, RogueForge uses the deterministic lifecycle contract documented in [CONTAINER_DEPLOYMENT.md](CONTAINER_DEPLOYMENT.md).
