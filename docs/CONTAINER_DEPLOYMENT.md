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
ROGUEFORGE_MEDIA_ROOT=/opt/media-server
ROGUEFORGE_COMPOSE_ROOT=/opt/media-server/compose
ROGUEFORGE_ENV_ROOT=/opt/media-server/compose
```

For a stack named `dozzle`, that layout resolves to:

```text
/opt/media-server/compose/dozzle/compose.yaml
/opt/media-server/compose/dozzle/.env
```

Administrators can point all roots at the same directory when their layout is flatter.

## Mounts

A typical Podman deployment mounts:

```text
/run/user/<UID>/podman/podman.sock -> /run/podman/podman.sock
/opt/media-server                  -> /opt/media-server
./data                             -> /opt/rogueforge/data
```

The installer derives the current UID rather than assuming UID 1000.

## Stack lifecycle contract

RogueForge deliberately uses deterministic Compose lifecycle operations:

```text
Start     -> up -d
Stop      -> down
Restart   -> down, then up -d
Recreate  -> down, then up -d
Update    -> pull, down, then up -d
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

The 0.9.1 testing milestone continues this with coalesced in-flight refreshes, targeted cache invalidation, bounded stats work and endpoint timing diagnostics.

## Network model

A common deployment uses:

```text
Container/network: http://rogueforge:7810
Host/LAN:          http://<server-ip>:17810
Shared network:    media-net
```

A reverse proxy can forward HTTPS traffic to `rogueforge:7810` on the shared network.

## Manual diagnostics

```bash
curl -fsS http://127.0.0.1:17810/health
podman inspect rogueforge --format '{{.Image}} {{.Config.Image}}'
podman exec rogueforge podman --remote --url unix:///run/podman/podman.sock info
```

Do not use `sudo podman` for a rootless deployment.
