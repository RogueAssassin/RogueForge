# Static Docker CLI and Compose v2 plugin for Docker hosts. Debian bookworm only packages the
# legacy Python docker-compose v1, which does not provide the `docker compose` subcommand
# RogueForge calls, and its docker.io package drags the whole daemon into the image.
FROM docker:28.3.3-cli AS docker-cli

FROM debian:bookworm-slim

LABEL org.opencontainers.image.source="https://github.com/RogueAssassin/RogueForge" \
      org.opencontainers.image.title="RogueForge" \
      org.opencontainers.image.description="Self-hosted operations console for Docker and Podman Compose stacks"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates podman python3 python3-dotenv python3-yaml tini \
    && rm -rf /var/lib/apt/lists/*

# Debian bookworm packages podman-compose 1.0.3, which rejects any stack whose service
# networks use the mapping form (for example `aliases:`) with "missing networks", and
# ignores `x-podman` and the PODMAN_COMPOSE_* settings RogueForge passes. Bundle a current
# upstream release instead; it is a single script with the two Python dependencies above.
ARG PODMAN_COMPOSE_VERSION=1.5.0
ARG PODMAN_COMPOSE_SHA256=7a39883eda17dbf8473e8ebdfd7d27a893bd518ea9583eeaaafee3cca7e50338
ADD --checksum=sha256:${PODMAN_COMPOSE_SHA256} --chmod=0755 \
    https://raw.githubusercontent.com/containers/podman-compose/v${PODMAN_COMPOSE_VERSION}/podman_compose.py \
    /usr/bin/podman-compose

COPY --from=docker-cli /usr/local/bin/docker /usr/bin/docker
COPY --from=docker-cli /usr/local/libexec/docker/cli-plugins/docker-compose /usr/libexec/docker/cli-plugins/docker-compose

WORKDIR /opt/rogueforge
COPY rogueforge.py setup-auth.py VERSION ./
COPY static ./static

# The workflow stamps rogueforge.py to the root VERSION before this image is built.
# Keep the Containerfile version-agnostic so releases never retain stale hard-coded tags.
RUN python3 -m py_compile rogueforge.py setup-auth.py \
    && python3 - <<'PY'
from pathlib import Path
import re
version=Path('VERSION').read_text(encoding='utf-8').strip()
source=Path('rogueforge.py').read_text(encoding='utf-8')
match=re.search(r'^VERSION="([^"]+)"$', source, re.M)
assert match and match.group(1)==version, f'packaged runtime version mismatch: {match.group(1) if match else "missing"} != {version}'
PY

ENV ROGUEFORGE_BIND=0.0.0.0 \
    ROGUEFORGE_PORT=7810 \
    ROGUEFORGE_ENGINE=podman \
    ROGUEFORGE_SOCKET=/run/podman/podman.sock \
    ROGUEFORGE_PODMAN_REMOTE=true \
    ROGUEFORGE_SCAN_DEPTH=4 \
    ROGUEFORGE_DISCOVERY_CACHE=10 \
    CONTAINER_HOST=unix:///run/podman/podman.sock

EXPOSE 7810
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7810/health', timeout=3)" || exit 1

# tini is PID 1 so SIGTERM stops RogueForge immediately (Python as PID 1 ignores it and
# waits for SIGKILL) and orphaned engine/compose child processes are reaped.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3", "/opt/rogueforge/rogueforge.py"]
