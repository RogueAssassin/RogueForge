# RogueForge 0.4.3

RogueForge 0.4.3 brings the GHCR deployment lifecycle to both Docker and rootless Podman.

## Highlights

- `./install.sh` automatically detects a usable Podman or Docker runtime.
- `./install.sh --engine podman` and `./install.sh --engine docker` provide explicit selection.
- Compose mounts the correct engine socket using `.env` values generated on the host.
- The application image includes clients for Podman Compose and Docker Compose stack operations.
- `upgrade.sh` remembers and uses the installation runtime.
- Clean, version-specific clone commands avoid local-change checkout failures.
- The GitHub banner is now permanent artwork without a release number.

## Upgrade from v0.4.1 or v0.4.2

```bash
cd /tmp
git clone --branch v0.4.3 --depth 1 \
  https://github.com/RogueAssassin/RogueForge.git rogueforge-upgrade-0.4.3
sudo cp -a /opt/media-server/rogueforge/compose.yaml \
  /opt/media-server/rogueforge/compose.yaml.pre-0.4.3
sudo install -m 0644 rogueforge-upgrade-0.4.3/compose.yaml \
  /opt/media-server/rogueforge/compose.yaml
sudo install -m 0755 rogueforge-upgrade-0.4.3/upgrade.sh \
  /opt/media-server/rogueforge/upgrade.sh
sudo chown -R "$(id -u):$(id -g)" /opt/media-server/rogueforge
cd /opt/media-server/rogueforge
./upgrade.sh 0.4.3
```

This preserves the existing administrator account and configuration.
