# RogueForge container deployment model

RogueForge is distributed as a multi-architecture GHCR image and supports Docker plus rootless Podman.

## Runtime model

For rootless Podman, RogueForge mounts the host user's API socket:

```text
Host:      /run/user/<UID>/podman/podman.sock
Container: /run/podman/podman.sock
```

Runtime inventory and container actions use the remote Podman socket. Compose-managed stack actions use the Compose provider against the same host engine context, so RogueForge does not accidentally create an isolated container store inside itself.

## Configurable roots

The mount root, Compose discovery root and environment-file root are independent:

```env
ROGUEFORGE_INSTALL_DIR=/opt/media-server/rogueforge
ROGUEFORGE_DATA_DIR=/opt/media-server/rogueforge/data
ROGUEFORGE_MEDIA_ROOT=/opt/media-server
ROGUEFORGE_COMPOSE_ROOT=/opt/media-server
ROGUEFORGE_ENV_ROOT=/opt/media-server
```

For a stack named `radarr`, that layout resolves to:

```text
/opt/media-server/radarr/compose.yaml
/opt/media-server/radarr/.env
```

RogueForge's own deployment remains isolated at `/opt/media-server/rogueforge` while the discovery root stays at `/opt/media-server`.

## Mounts

A typical Podman deployment mounts:

```text
/run/user/<UID>/podman/podman.sock -> /run/podman/podman.sock
/opt/media-server                  -> /opt/media-server
/opt/media-server/rogueforge/data -> /opt/rogueforge/data
```

The installer derives the current UID rather than assuming UID 1000.

## Stack lifecycle contract

RogueForge deliberately uses deterministic Compose lifecycle operations:

```text
Start     -> up -d, then verify stable running state
Stop      -> stop, then verify stopped state
Restart   -> restart, verify, then in-place reconcile if needed
Recreate  -> up -d --force-recreate, then verify
Update    -> pull, verify target image IDs, force-recreate in place, then verify/rollback
```

Update/replacement flows verify immutable image identity rather than treating a successful pull as a successful deployment.

For Podman, RogueForge invokes the compatible Compose provider directly for in-app stack actions and loads the stack's `.env` values into that process environment. This avoids relying on wrapper flags unsupported by older bundled Podman clients while the remote socket still targets the host daemon.

## Discovery

Active runtime Compose labels are authoritative. Filesystem scanning adds genuinely stopped stacks but suppresses duplicate definitions for already-active projects. Backups are stored outside the Compose discovery tree under `/tmp/rogueforge/`.

## Self-stack protection

The `rogueforge` project is intentionally protected from in-app lifecycle and editor actions. Manage RogueForge itself from the host deployment directory.

## Performance model

RogueForge uses:

- a unified dashboard snapshot for initial page state,
- a short shared engine inventory cache,
- cached Compose discovery,
- asynchronous CPU/RAM refresh,
- targeted refresh after lifecycle operations.

The stable 2.0.0 production baseline and 2.1.0 testing branch preserve the validated cache/coalescing model, bounded engine concurrency, on-demand logs and lightweight read-only RogueDashboard integration.

## Network model

A common deployment uses:

```text
Container/network: http://rogueforge:7810
Host/LAN:          http://<server-ip>:17810
Shared network:    media-net
```

A reverse proxy can forward HTTPS traffic to `rogueforge:7810` on the shared network.

RogueForge controls the container engine, so limit who can reach the published port. When the
reverse proxy is the only client, set `ROGUEFORGE_HOST_BIND=127.0.0.1` in `.env` and recreate the
container; `rogueforge:7810` stays reachable on the shared network.

## Container runtime behaviour

- `tini` runs as PID 1, so `podman stop`/`docker stop` end RogueForge immediately and finished
  engine or Compose child processes are reaped.
- `compose.yaml` defines the health check itself, so it is reported the same way under Podman
  and Docker. `/health` fails when the engine socket cannot be reached.
- The image bundles the Podman remote client with `podman-compose`, and a static Docker CLI with
  the Compose v2 plugin, so in-app stack actions work against either engine.
- `no-new-privileges`, a memory ceiling, a PID ceiling and log rotation are applied by default.
  `ROGUEFORGE_MEM_LIMIT` and `ROGUEFORGE_PIDS_LIMIT` adjust the ceilings.
- RogueForge runs as root inside its container because it must use the engine socket and edit
  stack files. Under rootless Podman that maps to the unprivileged account that owns the
  containers.

## Updates and rollback

`./update.sh` pulls the requested image before it changes any deployment file, so an unpublished
tag leaves the installation untouched. If the recreated container fails verification or its
health check, the previous `compose.yaml`, `.env` and image are restored automatically.

## Manual diagnostics

```bash
curl -fsS http://127.0.0.1:17810/health
podman inspect rogueforge --format '{{.Image}} {{.Config.Image}}'
podman exec rogueforge podman --remote --url unix:///run/podman/podman.sock info
```

Do not use `sudo podman` for a rootless deployment.


## Read-only RogueDashboard integration

RogueDashboard can query:

```text
http://rogueforge:7810/api/integrations/roguedashboard
```

This endpoint reuses RogueForge's existing cached dashboard snapshot and in-memory operation history. It does not create a second Docker/Podman polling loop and does not expose the engine socket, filesystem roots, administrator credentials or raw operation output.


## 2.0 API and state contract

RogueForge 2.0 established API version 2 and state schema version 1; 2.1.0 testing continues that contract. The stable read-only endpoints are:

```text
/api/v2/status
/api/v2/contract
```

They reuse the existing lightweight cached runtime model and do not introduce another engine polling loop.
