# Changelog

## 0.6.2 — Bulk container operations and GitHub identity favicon

- Replaced the temporary generated browser favicon with the RogueAssassin GitHub profile image used by the repository owner account.
- Added multi-select container rows with protected self-container exclusion.
- Added bulk Start, Stop, Restart, Update, Recreate, and Remove operations with per-container results and failure isolation.
- Added container sorting by name, state, project, and image.
- Added live CPU, memory, and network usage display to the Containers page.
- Added restart-policy visibility to authenticated container inspection.
- Added persistent action busy states and clearer aggregate feedback for bulk jobs.
- Kept all bulk mutations authenticated, CSRF-protected, and routed through the existing remote Podman/Compose execution layer.
- Updated Compose, `.env.example`, and first-install defaults to `ghcr.io/rogueassassin/rogueforge:0.6.2`.

## 0.6.1 — Container update awareness and live usage

- Added authenticated live container resource statistics.
- Added per-container image update checks by comparing the running container image ID with the current locally pulled image ID.
- Added Update All while continuing to exclude RogueForge itself from self-management.
- Added canonical RogueForge web logo assets and favicon hooks.
- Added action busy states so repeated clicks cannot accidentally queue duplicate container operations.

## 0.6.0 — Dockge-style container operations

- Expanded the Containers page with state-aware Start, Stop, Restart, Update, Recreate, Inspect, Logs, and Remove controls.
- Added Compose project/service metadata to container inventory so actions can target one service instead of recreating an entire stack.
- Added Compose-aware per-container Update: pull the selected service image, then run `up -d --no-deps --remove-orphans <service>` when the container belongs to a Compose project.
- Added per-service Recreate using `up -d --no-deps --force-recreate <service>`.
- Added safe single-service removal using Compose `rm -s -f <service>` while keeping the Compose definition intact.
- Added standalone-container image pulling without unsafe automatic recreation when the original run configuration cannot be guaranteed.
- Added authenticated container inspection with state, timestamps, image ID, command, mounts, networks, project and service metadata.
- Added RogueForge self-container protection so the application cannot stop, restart, update, recreate, or remove itself from inside its own request lifecycle.
- Added responsive container action layout and richer filtering by container name, image, project and service.
- Kept all mutations behind the existing signed-session and CSRF protections.
- Kept rootless Podman operations on the mounted FEILSBEASTSERVER host socket and retained Docker socket compatibility.
- Moved the new container feature surface into an extension layer so the validated 0.5.0 runtime/auth/Compose core remains unchanged underneath.
- Updated GHCR release-tag validation, Compose defaults, environment example and installer for 0.6.0.

## 0.5.0 — Rootless Podman command and deployment reliability

- Unified rootless Podman control around the mounted host Podman socket.
- Made Podman Compose commands explicitly inherit `CONTAINER_HOST`/`DOCKER_HOST` pointing at the mounted remote socket.
- Kept Podman container inventory, logs, and lifecycle actions on explicit `podman --remote --url ...` execution.
- Replaced destructive Compose restart (`down` followed by `up -d`) with native `restart`.
- Changed normal stack Stop to `compose stop` so it no longer removes the Compose project.
- Added an explicit Recreate action using `up -d --force-recreate`.
- Added a self-stack guard so RogueForge cannot stop, restart, recreate, pull, edit, or otherwise manage its own Compose project from inside itself.
- Added `managed` stack metadata so the UI clearly shows RogueForge as self-managed externally.
- Reloaded authoritative session/infrastructure state immediately after login and logout.
- Added authentication-file diagnostics for missing, unreadable, malformed, or invalid `auth.json` state.
- Added authenticated `/api/diagnostics` runtime checks for engine/socket, remote Podman CLI, stack root, icons and authentication state.
- Kept LAN HTTP cookies compatible while preserving `Secure` cookies when `X-Forwarded-Proto` is HTTPS.
- Updated Compose defaults to the 0.5.0 image and added `ROGUEFORGE_SELF_STACK=rogueforge`.
- Kept FEILSBEASTSERVER-compatible defaults: `/opt/media-server`, rootless UID 1000 socket example, port 17810, `media-net`, and the existing Rogue Dashboard icon path.
- Updated first installation to validate Compose before startup and to derive the rootless Podman socket from the actual installer user.
- Reworked `upgrade.sh` so future upgrades back up and update deployment files as well as the application image while preserving `.env` and `data/auth.json`.
- Added rollback restoration for the Compose definition, environment, auth record, setup helper and upgrader.
- Updated README and installation guidance for the one-time 0.4.x to 0.5.0 deployment bootstrap.

## 0.4.3 — Docker and Podman deployment parity

- Added automatic and explicit Docker/rootless Podman selection to first installation.
- Parameterized the engine socket mount, socket target, container host, and remote-Podman mode in Compose.
- Added Docker Compose support inside the GHCR application image for stack operations.
- Made `upgrade.sh` select the recorded Docker or Podman runtime automatically.
- Changed upgrade documentation to use clean, release-specific Git clones so local changes cannot block tag checkout.
- Reworked installation, update, restart, stop, start, and troubleshooting instructions for both runtimes.
- Replaced versioned GitHub artwork with a permanent version-free RogueForge banner.

## 0.4.2 — Login and lifecycle reliability

- Fixed LAN login by setting `Secure` session cookies only for requests forwarded as HTTPS.
- Kept secure cookies enabled behind Nginx Proxy Manager through `X-Forwarded-Proto`.
- Pre-filled the documented default username, `administrator`, in the login form.
- Added an in-place `upgrade.sh` with tagged-image selection, preflight pulling, environment backup, health verification, and rollback.
- Made startup health checks tolerate transient connection resets.
- Added a GHCR workflow guard that rejects release tags which differ from the application version.
- Reorganized the README around first installation, updating, restarting, stopping, and password recovery.
- Added refreshed v0.4.2 GitHub artwork.

## 0.4.1 — First-install GHCR deployment

- Replaced the legacy host-service installer with a rootless Podman first-install workflow.
- Added automatic creation of `/opt/media-server/rogueforge`, `.env`, `data/`, and `media-net` deployment state.
- Added configurable installation, stacks, icons, host port, public URL, network, image, and administrator values.
- Pinned production installation to the semantic `ghcr.io/rogueassassin/rogueforge:0.4.1` release.
- Added a v0.4.1 GitHub banner, corrected README, and first-release instructions.
- Kept GHCR pulling ahead of host changes so unavailable images do not leave partial installations.

## 0.4.0 — Security and distribution

- Added administrator provisioning with no default password.
- Added signed sessions, CSRF enforcement, and login throttling.
- Protected Compose viewing/editing, container logs, and lifecycle actions.
- Added login and logout interface states.
- Changed the default icon directory to `/opt/media-server/rogue-dashboard/app/static/icons`.
- Changed the default deployment image to `ghcr.io/rogueassassin/rogueforge`.
- Pinned clean deployments to the published immutable `sha-1b3e868` GHCR image until a semantic `0.4.0` tag is published.
- Added multi-architecture GHCR publishing through GitHub Actions.
- Added persistent authentication data volume.
- Added a guarded 0.3-to-0.4 GHCR migration with backup and rollback.

## 0.3.0 — Network and icons

- Added the `media-net` container deployment.
- Added configurable host port publishing with internal port 7810.
- Added local stack/container icons and generated fallbacks.
- Added Podman remote-client support.

## 0.2.3 — Rootless Podman correction

- Made the rootless owner's Podman CLI authoritative for inventory and controls.
- Corrected rootless home/runtime environment handling.
