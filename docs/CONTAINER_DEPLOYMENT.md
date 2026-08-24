# RogueForge on Docker, rootless Podman, and media-net

RogueForge 0.5.0 is distributed as a prebuilt GHCR image with a small host-side deployment bundle.

## Runtime model

For rootless Podman, RogueForge mounts the host user's Podman API socket into the application container:

```text
Host:      /run/user/<UID>/podman/podman.sock
Container: /run/podman/podman.sock
```

Container inventory, logs and lifecycle actions use explicit `podman --remote --url unix:///run/podman/podman.sock` execution. Compose operations run inside the RogueForge application container but receive `CONTAINER_HOST=unix:///run/podman/podman.sock`, which makes the Podman client operate remotely against the same host engine.

This keeps container and Compose actions in the same rootless Podman storage/context instead of accidentally using an isolated Podman store inside RogueForge.

## Default FEILSBEASTSERVER address model

```text
Container/network: http://rogueforge:7810
Host/LAN:          http://<server-ip>:17810
Public proxy:      https://manage.roguegaming.com.au
Shared network:    media-net
Stacks root:       /opt/media-server
```

Nginx Proxy Manager and RogueForge share `media-net`. NPM forwards to `rogueforge:7810`.

## Compose mounts

```text
/run/user/<UID>/podman/podman.sock -> /run/podman/podman.sock
/opt/media-server                 -> /opt/media-server
./data                            -> /opt/rogueforge/data
```

For FEILSBEASTSERVER the current owner UID is 1000, so the first path is `/run/user/1000/podman/podman.sock`. The installer writes the actual current UID to `.env` rather than depending on the example default.

## Self-stack protection

`/opt/media-server/rogueforge/compose.yaml` is intentionally discoverable, but the API marks the `rogueforge` project as `managed: false`. The web UI shows it as self-managed externally and does not present lifecycle/edit actions.

The backend also rejects attempts to manage the self stack, so a stale or malicious client cannot make RogueForge execute a command that stops/removes the container handling that request.

Manage RogueForge itself from the host:

```bash
cd /opt/media-server/rogueforge
podman-compose restart
```

## Stack action semantics

RogueForge 0.5.0 uses:

```text
Start     -> compose up -d
Stop      -> compose stop
Restart   -> compose restart
Pull      -> compose pull
Recreate  -> compose up -d --force-recreate
```

Restart no longer tears the project down. Recreate is a separate deliberate operation.

## First installation

```bash
git clone --branch v0.5.0 --depth 1 https://github.com/RogueAssassin/RogueForge.git RogueForge-0.5.0
cd RogueForge-0.5.0
chmod +x install.sh
./install.sh --engine podman
```

The installer validates the runtime/Compose client, enables the rootless socket, pulls the image before host changes, writes `.env`, provisions authentication, validates Compose, starts the service and checks health.

## Persistent authentication

The host file:

```text
/opt/media-server/rogueforge/data/auth.json
```

is mounted at:

```text
/opt/rogueforge/data/auth.json
```

inside the application. It is preserved by normal upgrades and recreates.

## Local icons

The default icon folder is:

```text
/opt/media-server/rogue-dashboard/app/static/icons
```

## Manual lifecycle

```bash
cd /opt/media-server/rogueforge
podman-compose config
podman-compose pull
podman-compose up -d
podman-compose restart
podman-compose logs -f
podman-compose down
```

Do not use `sudo podman` for a rootless deployment because it selects a different container store/socket.
