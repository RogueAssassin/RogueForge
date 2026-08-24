# Publishing RogueForge to GHCR

The repository includes `.github/workflows/container.yml`. It publishes:

```text
ghcr.io/rogueassassin/rogueforge:<version>
ghcr.io/rogueassassin/rogueforge:<major>.<minor>
ghcr.io/rogueassassin/rogueforge:latest
ghcr.io/rogueassassin/rogueforge:sha-<commit>
```

Images are built for `linux/amd64` and `linux/arm64`.

For tag builds, the workflow imports `rogueforge.py` and refuses publication when the Git tag and application version differ. The 0.5.0 source reports `VERSION = "0.5.0"`, so the semantic release tag must be `v0.5.0`.

## Publish 0.5.0

After the final 0.5.0 source is on `main`:

```bash
git pull --ff-only origin main
git tag v0.5.0
git push origin v0.5.0
```

The tag-triggered workflow publishes the immutable `0.5.0` and `0.5` tags. The default branch workflow also maintains `latest` and commit-SHA tags.

Confirm the workflow succeeds in the repository Actions view before upgrading production to the semantic tag.

## Pulling the release

```bash
podman pull ghcr.io/rogueassassin/rogueforge:0.5.0
```

## Package authentication

If the package is public, no GHCR login is needed. If private, authenticate with a package-read token through stdin and do not place the token in Compose YAML, `.env`, shell history, or the repository.

## Local development image

The production `compose.yaml` pulls GHCR. To build locally, apply the included override:

```bash
podman-compose -f compose.yaml -f compose.build.yaml up -d --build
```
