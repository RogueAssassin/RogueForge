# RogueForge 0.7.0 — Live Operations

RogueForge 0.7.0 adds live operational access on top of the 0.6.2 container-management base.

## Highlights

- Live container logs over authenticated Server-Sent Events.
- Pause/resume, search, clear, follow and download controls for streamed logs.
- Authenticated container terminal/exec sessions.
- Automatic Bash-to-`sh` shell fallback.
- CSRF-protected terminal creation, input and close operations.
- Automatic inactive terminal cleanup and explicit process cleanup on close.
- Continued support for rootless Podman through the mounted host socket and Docker through the Docker socket.
- Existing lifecycle, bulk actions, update checks, resource statistics and self-protection remain intact.

## FEILSBEASTSERVER upgrade

```bash
cd /opt/media-server/rogueforge
./upgrade.sh latest
curl -sS http://127.0.0.1:17810/health && echo
podman logs --tail 100 rogueforge
```

Expected health response:

```json
{"ok":true,"version":"0.7.0"}
```

After deployment, sign in and test **Live logs** and **Terminal** on a non-critical running container first.

## Remaining 0.7.x work

- Real-time Compose/Pull/Update action output.
- Persistent operations history.
- Resumable long-running jobs across navigation/reload.
- Runtime-supported action cancellation.
- PTY/terminal resize support for full-screen interactive applications.
