# Publishing RogueForge to GHCR

The repository includes `.github/workflows/container.yml`. It publishes:

```text
ghcr.io/rogueassassin/rogueforge:<version>
ghcr.io/rogueassassin/rogueforge:<major>.<minor>
ghcr.io/rogueassassin/rogueforge:latest
ghcr.io/rogueassassin/rogueforge:sha-<commit>
```

Images are built for `linux/amd64` and `linux/arm64`.

## First publication

1. Commit the 0.4.1 source and workflow to the `main` branch.
2. Push a `v0.4.1` tag.
3. Open the repository's **Actions** tab and confirm the publishing workflow succeeds.
4. Open the resulting package and set package visibility to public if it should be pulled without authentication.

Example tag:

```bash
git tag v0.4.1
git push origin main v0.4.1
```

The workflow uses GitHub's short-lived `GITHUB_TOKEN`; no personal access token is stored in the repository.

## Pulling a public image

```bash
podman pull ghcr.io/rogueassassin/rogueforge:0.4.1
```

## Pulling while the package is private

Create a GitHub token with read access to packages, then authenticate on the server:

```bash
printf '%s' "$GHCR_TOKEN" | podman login ghcr.io -u RogueAssassin --password-stdin
podman pull ghcr.io/rogueassassin/rogueforge:0.4.1
```

Do not place the token in Compose YAML, `.env`, shell history, or the repository.

## Local development image

The production `compose.yaml` pulls GHCR. To build locally, apply the included override:

```bash
podman-compose -f compose.yaml -f compose.build.yaml up -d --build
```
