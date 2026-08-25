# Publishing RogueForge to GHCR

The repository includes `.github/workflows/container.yml`. Each current release publishes:

```text
ghcr.io/rogueassassin/rogueforge:latest
ghcr.io/rogueassassin/rogueforge:0.8.4
ghcr.io/rogueassassin/rogueforge:v0.8.4
ghcr.io/rogueassassin/rogueforge:084
ghcr.io/rogueassassin/rogueforge:sha-<commit>
```

Images are built for `linux/amd64` and `linux/arm64`.

## Release metadata

The canonical release number is stored in the root `VERSION` file. CI stamps and verifies that value in `rogueforge.py` during validation **and again in the publish checkout before the container image is built**. This guarantees the UI and `/health` runtime version match the GHCR release aliases.

After a successful multi-architecture publish, CI creates the matching immutable Git tag (`v<version>`) when it does not already exist.

`latest` tracks the current release line on `main`. Semantic (`0.8.4`) and v-prefixed (`v0.8.4`) tags are convenient pinned aliases, compact (`084`) supports short update references, and SHA tags provide exact build identification.

## Updating

```bash
cd /opt/media-server/rogueforge
./update.sh latest
```

Pinned semantic release:

```bash
./update.sh 0.8.4
```

The updater downloads current deployment tooling from `main`, then pulls the requested runtime image tag. This keeps updater/Compose compatibility fixes available when rolling back to a historical runtime image.

## Pulling directly

```bash
podman pull ghcr.io/rogueassassin/rogueforge:0.8.4
```

## Package authentication

If the package is public, no GHCR login is needed. If private, authenticate with a package-read token through stdin and do not place the token in Compose YAML, `.env`, shell history, or the repository.

## Local development image

```bash
podman-compose -f compose.yaml -f compose.build.yaml up -d --build
```
