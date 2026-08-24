# RogueForge 0.4.2

RogueForge 0.4.2 fixes administrator sessions across both LAN HTTP and Nginx Proxy Manager HTTPS access, and adds a repeatable upgrade lifecycle.

## Fixes

- Direct `http://server:17810` login no longer receives an unusable Secure-only cookie.
- Proxied HTTPS requests still receive Secure, HttpOnly, SameSite cookies.
- The default `administrator` username is visible in the login form.
- Startup verification tolerates temporary connection resets while the container initializes.

## Operations

- First install: `./install.sh`
- Upgrade to a pinned release: `./upgrade.sh 0.4.2`
- Upgrade to the mutable channel: `./upgrade.sh latest`
- Restart: `podman-compose restart`
- Stop: `podman-compose down`
- Start: `podman-compose up -d`

The upgrader preserves `.env` and `data/auth.json`, pulls before switching images, and restores the previous image when health verification fails.

## Publishing

Push `main`, then create and push `v0.4.2`. The workflow verifies that `v0.4.2` matches the application’s internal version before publishing multi-architecture GHCR tags.
