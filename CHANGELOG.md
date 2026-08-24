# Changelog

## 0.4.0 — Security and distribution

- Added administrator provisioning with no default password.
- Added signed sessions, CSRF enforcement, and login throttling.
- Protected Compose viewing/editing, container logs, and lifecycle actions.
- Added login and logout interface states.
- Changed the default icon directory to `/opt/media-server/rogue-dashboard/app/static/icons`.
- Changed the default deployment image to `ghcr.io/rogueassassin/rogueforge`.
- Added multi-architecture GHCR publishing through GitHub Actions.
- Added persistent authentication data volume.

## 0.3.0 — Network and icons

- Added the `media-net` container deployment.
- Added configurable host port publishing with internal port 7810.
- Added local stack/container icons and generated fallbacks.
- Added Podman remote-client support.

## 0.2.3 — Rootless Podman correction

- Made the rootless owner's Podman CLI authoritative for inventory and controls.
- Corrected rootless home/runtime environment handling.
