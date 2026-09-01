FROM debian:bookworm-slim

LABEL org.opencontainers.image.source="https://github.com/RogueAssassin/RogueForge" \
      org.opencontainers.image.title="RogueForge" \
      org.opencontainers.image.description="Self-hosted operations console for Docker and Podman Compose stacks"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates docker.io docker-compose podman podman-compose python3 \
    && rm -rf /var/lib/apt/lists/*

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
match=re.search(r'^VERSION="([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?)"
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
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7810/health', timeout=3)" || exit 1
CMD ["python3", "/opt/rogueforge/rogueforge.py"]
, source, re.M)
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
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7810/health', timeout=3)" || exit 1
CMD ["python3", "/opt/rogueforge/rogueforge.py"]
