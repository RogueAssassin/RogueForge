# Publishing RogueForge to GHCR

The repository includes `.github/workflows/container.yml`. Each current release publishes:

```text
ghcr.io/rogueassassin/rogueforge:latest
ghcr.io/rogueassassin/rogueforge:0.8.3
ghcr.io/rogueassassin/rogueforge:v0.8.3
ghcr.io/rogueassassin/rogueforge:083
ghcr.io/rogueassassin/rogueforge:sha-<commit>
```

Images are built for `linux/amd64` and `linux/arm64`.

## Release metadata

The canonical release number is stored in the root `VERSION` file. CI validates the packaged single-file runtime using that version, creates the matching immutable Git tag (`v<version>`) when it does not already exist, and publishes all GHCR aliases from the same validated build.

`latest` tracks the current release line on `main`. Semantic (`0.8.3`) and v-prefixed (`v0.8.3`) tags are convenient pinned aliases, while compact (`083`) is provided for short update references. SHA tags remain available for exact build identification.

## Updating

Recommended:

```bash
cd /opt/media-server/rogueforge
./update.sh latest
```

Pinned semantic release:

```bash
./update.sh 0.8.3
```

The updater always downloads current deployment tooling from `main`, then pulls the requested runtime image tag. This means updater and Compose compatibility fixes remain available even when rolling back to a historical RogueForge runtime image.

## Pulling directly

```bash
podman pull ghcr.io/rogueassassin/rogueforge:0.8.3
```

## Package authentication

If the package is public, no GHCR login is needed. If private, authenticate with a package-read token through stdin and do not place the token in Compose YAML, `.env`, shell history, or the repository.

## Local development image

The production `compose.yaml` pulls GHCR. To build locally, apply the included override:

```bash
podman-compose -f compose.yaml -f compose.build.yaml up -d --build
```
