# Changelog

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
