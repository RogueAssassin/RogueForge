# RogueForge 0.5.0 release notes

RogueForge 0.5.0 is the rootless Podman reliability release.

## Fixed

- Compose actions now target the same mounted host Podman socket as container actions.
- Restart uses native Compose restart instead of `down` followed by `up`.
- Stop uses `compose stop` and no longer removes the project.
- Recreate is an explicit separate operation.
- RogueForge cannot manage its own Compose project from inside the running application.
- Login/logout now refresh authoritative server session state immediately.
- Authentication failures expose useful local auth-file diagnostics without exposing secrets.
- The deployment upgrader now updates the deployment bundle and image together while preserving `.env` and `data/auth.json`.

## FEILSBEASTSERVER defaults

```text
Stacks:       /opt/media-server
Install:      /opt/media-server/rogueforge
Podman socket:/run/user/1000/podman/podman.sock
Host port:    17810
Network:      media-net
Public URL:   https://manage.roguegaming.com.au
```

## Upgrade from 0.4.x

Because the old upgrader does not update itself or `compose.yaml`, copy the 0.5.0 `compose.yaml` and `upgrade.sh` into `/opt/media-server/rogueforge` once, preserving `.env` and `data/auth.json`, then run:

```bash
cd /opt/media-server/rogueforge
./upgrade.sh 0.5.0
```

See `README.md` and `docs/INSTALL.md` for the complete backup/bootstrap commands.

## Release tag

The GHCR workflow requires the tag to match `rogueforge.VERSION`. Publish this release with `v0.5.0` after confirming `main` is final.
