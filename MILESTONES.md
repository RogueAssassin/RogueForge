# RogueForge milestones

## 0.4.1 — First-install release

- [x] GHCR-first rootless Podman installer.
- [x] Default `/opt/media-server/rogueforge` deployment layout.
- [x] Automatic persistent folders, local administrator, and shared network setup.
- [x] Semantic GHCR release documentation.
- [x] Updated GitHub banner and README.

## 0.1 — Foundation

Status: Complete

- Docker and Podman socket detection.
- Compose stack discovery and lifecycle actions.
- Container inventory, logs, and controls.
- Safe Compose validation and backup.

## 0.2 — Operate

Status: Complete

- Dockge-inspired operations console.
- Rootless Podman ownership support.
- Custom installation and stack paths.
- Nginx Proxy Manager deployment guidance.

## 0.3 — Network and identity

Status: Complete

- First-class container deployment on external `media-net`.
- Stable `rogueforge:7810` service discovery for NPM.
- Configurable host-side LAN port.
- Local Rogue Dashboard-compatible workload icons.
- Podman remote control through a mounted Unix socket.

## 0.4 — Security and distribution

Status: Complete

- Locally provisioned administrator account.
- PBKDF2-SHA256 password hashing with per-account salt.
- Signed, expiring, HttpOnly, SameSite session cookies.
- Secure cookies when the configured public URL uses HTTPS.
- CSRF validation on privileged operations.
- Login attempt throttling.
- Read-only dashboard without authentication.
- Protected Compose source, logs, and workload controls.
- GHCR deployment and multi-architecture publishing workflow.

## 0.5 — Observe

Status: Planned

- HTTP, TCP, DNS, ping, certificate, and container health checks.
- Uptime history and response-time charts.
- Notification providers and maintenance windows.
- Public and private status pages.

## 0.6 — Scale

Status: Planned

- Multi-host outbound agents.
- Roles beyond the initial administrator account.
- Audit history and approval workflows.
- Git-backed stack delivery and rollback.
