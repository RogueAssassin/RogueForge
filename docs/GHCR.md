# Publishing RogueForge to GHCR

RogueForge uses two persistent branches:

- `main` — production only.
- `testing` — active development and server validation.

## Production channel

A successful publish from `main` builds `linux/amd64` and `linux/arm64` images and publishes:

```text
ghcr.io/rogueassassin/rogueforge:latest
ghcr.io/rogueassassin/rogueforge:<VERSION>
ghcr.io/rogueassassin/rogueforge:v<VERSION>
ghcr.io/rogueassassin/rogueforge:<compact-version>
ghcr.io/rogueassassin/rogueforge:sha-<commit>
```

For 1.0.0 the compact tag is `100`. Production CI may create the immutable Git tag `v<VERSION>` after a successful publish.

## Testing channel

Every validated push to `testing` publishes:

```text
ghcr.io/rogueassassin/rogueforge:testing
ghcr.io/rogueassassin/rogueforge:sha-<commit>
```

The testing branch never updates `:latest`, semantic/compact production aliases, or production Git tags.

## Release metadata

The canonical release number is stored in the root `VERSION` file. CI stamps and verifies that value in `rogueforge.py` before building the image.

## Updating

Production:

```bash
cd /opt/media-server/rogueforge
./update.sh latest
```

Permanent testing channel:

```bash
cd /opt/media-server/rogueforge
./update.sh testing
```

Pinned semantic production release:

```bash
./update.sh 1.0.0
```

The updater verifies the immutable pulled image ID against the image ID of the newly running RogueForge container before reporting success.

## Pulling directly

```bash
podman pull ghcr.io/rogueassassin/rogueforge:testing
podman pull ghcr.io/rogueassassin/rogueforge:1.0.0
```

## Package authentication

If the package is public, no GHCR login is needed. If private, authenticate with a package-read token through stdin and do not place the token in Compose YAML, `.env`, shell history, or the repository.
