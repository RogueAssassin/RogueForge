# RogueForge security

## Administrator provisioning

RogueForge has no default username/password pair. Provision an account locally:

```bash
python3 setup-auth.py --username administrator
```

The resulting `data/auth.json` contains a salted PBKDF2-SHA256 hash and random session-signing secret. It does not contain the password.

Use `--generate` to create a random 24-character password that is displayed once:

```bash
python3 setup-auth.py --username administrator --generate
```

Running the provisioner again replaces the password and invalidates every existing session.

## Protected operations

Authentication and a valid CSRF token are required for:

- Starting, stopping, restarting, or pulling stacks.
- Starting, stopping, or restarting containers.
- Reading container logs.
- Reading or replacing Compose configuration.

The overview, stack summary, and container inventory remain read-only without authentication.

## Reverse proxy requirements

- Use HTTPS.
- Keep `ROGUEFORGE_PUBLIC_URL` set to the HTTPS public address so cookies receive the `Secure` attribute.
- Do not expose the Podman socket over TCP.
- Keep the host-side RogueForge port restricted to the trusted LAN.
- Nginx Proxy Manager may add an additional Access List as defence in depth.

## Reporting vulnerabilities

Do not publish credentials, session cookies, Compose secrets, container logs, or exploit details in a public issue. Contact the repository owner privately before disclosure.


## Browser response hardening

RogueForge 0.9.3 sends a consistent baseline of browser security headers from the application server:

- `X-Frame-Options: DENY` to prevent clickjacking in frames.
- `Referrer-Policy: no-referrer` to avoid leaking management URLs.
- `Permissions-Policy` disables camera, microphone and geolocation access.
- `Cross-Origin-Opener-Policy: same-origin` isolates the management browsing context.
- `X-Content-Type-Options: nosniff` remains enabled for API and static responses.

TLS/HSTS and trusted-forwarded-header policy should continue to be enforced by the administrator's reverse proxy.


## Runtime session and engine limits

RogueForge 0.9.4 bounds engine-detail and interactive-session work. Administrators can tune `ROGUEFORGE_ENGINE_DETAIL_CONCURRENCY`, `ROGUEFORGE_MAX_TERMINALS`, `ROGUEFORGE_TERMINAL_TTL`, `ROGUEFORGE_TERMINAL_MAX_LIFETIME` and `ROGUEFORGE_MAX_LOG_STREAMS`.

The defaults are intentionally conservative for a single-host management service. Raising these limits increases concurrent work against the Docker/Podman socket and should only be done when the host has sufficient capacity.
