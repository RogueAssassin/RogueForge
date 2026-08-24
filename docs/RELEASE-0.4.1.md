# RogueForge 0.4.1

RogueForge 0.4.1 makes the GHCR container the standard first-install path.

## Highlights

- Installs into `/opt/media-server/rogueforge` by default.
- Creates `.env`, `data/`, Compose configuration, and `media-net` automatically.
- Uses the rootless Podman owner’s UID and socket so existing containers remain visible.
- Pulls the release image before writing host deployment state.
- Provisions the first administrator during installation.
- Keeps the internal NPM address stable at `http://rogueforge:7810`.
- Defaults LAN access to the distinctive host port `17810`.
- Reuses Rogue Dashboard’s local icon directory when present.
- Adds a refreshed GitHub README and v0.4.1 banner.

## Image

```text
ghcr.io/rogueassassin/rogueforge:0.4.1
```

Architectures: `linux/amd64`, `linux/arm64`.

## First installation

```bash
git clone https://github.com/RogueAssassin/RogueForge.git
cd RogueForge
git checkout v0.4.1
chmod +x install.sh
./install.sh
```

Run as the account that owns the rootless Podman containers, not with `sudo`.

## Publication checklist

1. Commit the v0.4.1 source and banner.
2. Push `main`.
3. Create and push the `v0.4.1` tag.
4. Confirm the container workflow publishes `0.4.1`, `0.4`, `latest`, and the commit tag.
5. Confirm the GHCR package is public.
6. Test the documented first installation on a clean rootless Podman host.
