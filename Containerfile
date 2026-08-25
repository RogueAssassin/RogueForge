FROM debian:bookworm-slim

LABEL org.opencontainers.image.source="https://github.com/RogueAssassin/RogueForge" \
      org.opencontainers.image.title="RogueForge" \
      org.opencontainers.image.description="Self-hosted operations console for Docker and Podman Compose stacks"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates docker.io docker-compose podman podman-compose python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/rogueforge
COPY rogueforge.py ./rogueforge.py
COPY rogueforge_ext.py ./rogueforge_ext.py
COPY rogueforge_discovery.py ./rogueforge_discovery.py
COPY rogueforge_live.py ./rogueforge_live.py
COPY rogueforge_v071.py ./rogueforge_v071.py
COPY setup-auth.py ./setup-auth.py
COPY static ./static

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

CMD ["python3", "/opt/rogueforge/rogueforge_v071.py"]
