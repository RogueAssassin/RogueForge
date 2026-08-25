#!/usr/bin/env bash
set -Eeuo pipefail
VERSION=0.8.3
INSTALL_DIR=${ROGUEFORGE_INSTALL_DIR:-/opt/media-server/rogueforge}
STACKS_DIR=${ROGUEFORGE_STACKS_DIR:-/opt/media-server}
HOST_PORT=${ROGUEFORGE_HOST_PORT:-17810}
PUBLIC_URL=${ROGUEFORGE_PUBLIC_URL:-https://manage.roguegaming.com.au}
NETWORK=${ROGUEFORGE_NETWORK:-media-net}
USERNAME=${ROGUEFORGE_ADMIN_USERNAME:-administrator}
ENGINE=${ROGUEFORGE_DEPLOY_ENGINE:-auto}
[[ $EUID -ne 0 ]] || { echo "Run as the account that owns the containers, not root/sudo." >&2; exit 1; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --engine) ENGINE=$2; shift 2;; --install-dir) INSTALL_DIR=$2; shift 2;; --stacks-dir) STACKS_DIR=$2; shift 2;; --host-port) HOST_PORT=$2; shift 2;; --public-url) PUBLIC_URL=$2; shift 2;; --network) NETWORK=$2; shift 2;; --username) USERNAME=$2; shift 2;; --yes) shift;; *) echo "Unknown option: $1" >&2; exit 2;;
  esac
done
for c in curl python3; do command -v "$c" >/dev/null || { echo "Missing: $c" >&2; exit 2; }; done
if [[ $ENGINE == auto ]]; then
  if command -v podman >/dev/null && podman info >/dev/null 2>&1; then ENGINE=podman
  elif command -v docker >/dev/null && docker info >/dev/null 2>&1; then ENGINE=docker
  else echo "No working Podman or Docker runtime found." >&2; exit 2; fi
fi
[[ $ENGINE == podman || $ENGINE == docker ]] || { echo "--engine must be podman or docker" >&2; exit 2; }
COMPOSE=podman-compose; [[ $ENGINE == docker ]] && COMPOSE=docker-compose
command -v "$COMPOSE" >/dev/null || { echo "Missing: $COMPOSE" >&2; exit 2; }
mkdir -p "$INSTALL_DIR/data"; cd "$INSTALL_DIR"
BASE=https://raw.githubusercontent.com/RogueAssassin/RogueForge/main
for f in compose.yaml update.sh setup-auth.py; do curl -fsSL "$BASE/$f" -o "$f"; done
chmod +x update.sh setup-auth.py
if [[ $ENGINE == podman ]]; then
  uid=$(id -u); sock="/run/user/$uid/podman/podman.sock"; systemctl --user enable --now podman.socket >/dev/null 2>&1 || true
  [[ -S $sock ]] || { echo "Rootless Podman socket not found: $sock" >&2; exit 2; }
  cat > .env <<EOF
ROGUEFORGE_HOST_PORT=$HOST_PORT
ROGUEFORGE_IMAGE=ghcr.io/rogueassassin/rogueforge:$VERSION
ROGUEFORGE_DEPLOY_ENGINE=podman
ROGUEFORGE_ENGINE=podman
ROGUEFORGE_SOCKET_SOURCE=$sock
ROGUEFORGE_SOCKET_TARGET=/run/podman/podman.sock
ROGUEFORGE_CONTAINER_HOST=unix:///run/podman/podman.sock
ROGUEFORGE_PODMAN_REMOTE=true
ROGUEFORGE_STACKS_DIR=$STACKS_DIR
ROGUEFORGE_SCAN_DEPTH=4
ROGUEFORGE_DISCOVERY_CACHE=10
ROGUEFORGE_ICONS_DIR=$STACKS_DIR/rogue-dashboard/app/static/icons
ROGUEFORGE_SELF_STACK=rogueforge
ROGUEFORGE_PUBLIC_URL=$PUBLIC_URL
ROGUEFORGE_NETWORK=$NETWORK
EOF
else
  cat > .env <<EOF
ROGUEFORGE_HOST_PORT=$HOST_PORT
ROGUEFORGE_IMAGE=ghcr.io/rogueassassin/rogueforge:$VERSION
ROGUEFORGE_DEPLOY_ENGINE=docker
ROGUEFORGE_ENGINE=docker
ROGUEFORGE_SOCKET_SOURCE=/var/run/docker.sock
ROGUEFORGE_SOCKET_TARGET=/var/run/docker.sock
ROGUEFORGE_CONTAINER_HOST=unix:///var/run/docker.sock
ROGUEFORGE_PODMAN_REMOTE=false
ROGUEFORGE_STACKS_DIR=$STACKS_DIR
ROGUEFORGE_SCAN_DEPTH=4
ROGUEFORGE_DISCOVERY_CACHE=10
ROGUEFORGE_ICONS_DIR=$STACKS_DIR/rogue-dashboard/app/static/icons
ROGUEFORGE_SELF_STACK=rogueforge
ROGUEFORGE_PUBLIC_URL=$PUBLIC_URL
ROGUEFORGE_NETWORK=$NETWORK
EOF
fi
if ! $ENGINE network exists "$NETWORK" >/dev/null 2>&1; then $ENGINE network create "$NETWORK" >/dev/null; fi
if [[ ! -f data/auth.json ]]; then python3 setup-auth.py --username "$USERNAME"; fi
$ENGINE pull "ghcr.io/rogueassassin/rogueforge:$VERSION"
$COMPOSE -f compose.yaml up -d --remove-orphans
for _ in {1..30}; do curl -fsS "http://127.0.0.1:$HOST_PORT/health" && { echo; echo "RogueForge $VERSION installed at $INSTALL_DIR"; exit 0; }; sleep 2; done
echo "RogueForge did not pass its health check." >&2; $ENGINE logs --tail 100 rogueforge >&2 || true; exit 1
