#!/usr/bin/env bash
set -Eeuo pipefail

VERSION=0.6.2
INSTALL_DIR=${ROGUEFORGE_INSTALL_DIR:-/opt/media-server/rogueforge}
STACKS_DIR=${ROGUEFORGE_STACKS_DIR:-/opt/media-server}
ICONS_DIR=${ROGUEFORGE_ICONS_DIR:-/opt/media-server/rogue-dashboard/app/static/icons}
IMAGE=${ROGUEFORGE_IMAGE:-ghcr.io/rogueassassin/rogueforge:$VERSION}
HOST_PORT=${ROGUEFORGE_HOST_PORT:-17810}
PUBLIC_URL=${ROGUEFORGE_PUBLIC_URL:-https://manage.roguegaming.com.au}
NETWORK=${ROGUEFORGE_NETWORK:-media-net}
USERNAME=${ROGUEFORGE_ADMIN_USERNAME:-administrator}
DEPLOY_ENGINE=auto
ASSUME_YES=false

usage() {
  cat <<'EOF'
RogueForge first-install helper

Usage: ./install.sh [options]
  --engine auto|podman|docker
  --install-dir PATH
  --stacks-dir PATH
  --icons-dir PATH
  --image IMAGE
  --host-port PORT
  --public-url URL
  --network NAME
  --username NAME
  --yes
EOF
}

while (($#)); do
  case "$1" in
    --engine) DEPLOY_ENGINE=${2:?Missing engine}; shift 2 ;;
    --install-dir) INSTALL_DIR=${2:?Missing path}; shift 2 ;;
    --stacks-dir) STACKS_DIR=${2:?Missing path}; shift 2 ;;
    --icons-dir) ICONS_DIR=${2:?Missing path}; shift 2 ;;
    --image) IMAGE=${2:?Missing image}; shift 2 ;;
    --host-port) HOST_PORT=${2:?Missing port}; shift 2 ;;
    --public-url) PUBLIC_URL=${2:?Missing URL}; shift 2 ;;
    --network) NETWORK=${2:?Missing network}; shift 2 ;;
    --username) USERNAME=${2:?Missing username}; shift 2 ;;
    --yes) ASSUME_YES=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ $EUID -ne 0 ]] || { echo "Run as the container owner, not sudo/root." >&2; exit 1; }
for command in python3 curl sudo awk; do command -v "$command" >/dev/null || { echo "Missing: $command" >&2; exit 2; }; done
[[ $DEPLOY_ENGINE =~ ^(auto|podman|docker)$ ]] || { echo "Invalid engine" >&2; exit 2; }
[[ $HOST_PORT =~ ^[0-9]+$ ]] && ((HOST_PORT > 0 && HOST_PORT < 65536)) || { echo "Invalid host port" >&2; exit 2; }
SOURCE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
for file in compose.yaml setup-auth.py upgrade.sh .env.example; do [[ -f $SOURCE/$file ]] || { echo "Missing release file: $file" >&2; exit 2; }; done

if [[ $DEPLOY_ENGINE == auto ]]; then
  if command -v podman >/dev/null && podman info >/dev/null 2>&1; then DEPLOY_ENGINE=podman
  elif command -v docker >/dev/null && docker info >/dev/null 2>&1; then DEPLOY_ENGINE=docker
  else echo "No usable container runtime found." >&2; exit 2; fi
fi

if [[ $DEPLOY_ENGINE == podman ]]; then
  command -v podman-compose >/dev/null || { echo "podman-compose is required." >&2; exit 2; }
  ENGINE=(podman); COMPOSE=(podman-compose)
  systemctl --user enable --now podman.socket
  SOCKET_SOURCE="/run/user/$(id -u)/podman/podman.sock"
  SOCKET_TARGET=/run/podman/podman.sock
  CONTAINER_HOST=unix:///run/podman/podman.sock
  PODMAN_REMOTE=true
else
  ENGINE=(docker)
  if docker compose version >/dev/null 2>&1; then COMPOSE=(docker compose); else COMPOSE=(docker-compose); fi
  SOCKET_SOURCE=/var/run/docker.sock; SOCKET_TARGET=/var/run/docker.sock
  CONTAINER_HOST=unix:///var/run/docker.sock; PODMAN_REMOTE=false
fi

[[ -S $SOCKET_SOURCE ]] || { echo "Container socket not found: $SOCKET_SOURCE" >&2; exit 2; }
"${ENGINE[@]}" pull "$IMAGE"
[[ ! -e $INSTALL_DIR/compose.yaml && ! -e $INSTALL_DIR/data/auth.json ]] || { echo "Existing installation found; use upgrade.sh." >&2; exit 3; }

if [[ $ASSUME_YES != true ]]; then
  printf 'Install RogueForge %s to %s using %s? [y/N] ' "$VERSION" "$INSTALL_DIR" "$DEPLOY_ENGINE"
  read -r answer; [[ $answer == y || $answer == Y ]] || exit 0
fi

sudo install -d -m 0755 "$INSTALL_DIR" "$STACKS_DIR"
sudo install -d -m 0700 "$INSTALL_DIR/data"
sudo install -m 0644 "$SOURCE/compose.yaml" "$INSTALL_DIR/compose.yaml"
sudo install -m 0644 "$SOURCE/setup-auth.py" "$INSTALL_DIR/setup-auth.py"
sudo install -m 0644 "$SOURCE/.env.example" "$INSTALL_DIR/.env.example"
sudo install -m 0755 "$SOURCE/upgrade.sh" "$INSTALL_DIR/upgrade.sh"
sudo chown -R "$(id -u):$(id -g)" "$INSTALL_DIR"

cat > "$INSTALL_DIR/.env" <<EOF
ROGUEFORGE_HOST_PORT=$HOST_PORT
ROGUEFORGE_IMAGE=$IMAGE
ROGUEFORGE_DEPLOY_ENGINE=$DEPLOY_ENGINE
ROGUEFORGE_ENGINE=$DEPLOY_ENGINE
ROGUEFORGE_SOCKET_SOURCE=$SOCKET_SOURCE
ROGUEFORGE_SOCKET_TARGET=$SOCKET_TARGET
ROGUEFORGE_CONTAINER_HOST=$CONTAINER_HOST
ROGUEFORGE_PODMAN_REMOTE=$PODMAN_REMOTE
ROGUEFORGE_STACKS_DIR=$STACKS_DIR
ROGUEFORGE_ICONS_DIR=$ICONS_DIR
ROGUEFORGE_SELF_STACK=rogueforge
ROGUEFORGE_PUBLIC_URL=$PUBLIC_URL
ROGUEFORGE_NETWORK=$NETWORK
EOF
chmod 600 "$INSTALL_DIR/.env"
cd "$INSTALL_DIR"
python3 setup-auth.py --username "$USERNAME"
chmod 700 data && chmod 600 data/auth.json
"${ENGINE[@]}" network inspect "$NETWORK" >/dev/null 2>&1 || "${ENGINE[@]}" network create "$NETWORK"
"${COMPOSE[@]}" config >/dev/null
"${COMPOSE[@]}" pull
"${COMPOSE[@]}" up -d
curl --fail --silent --show-error --retry 20 --retry-delay 2 --retry-all-errors "http://127.0.0.1:$HOST_PORT/health" >/dev/null

echo "RogueForge $VERSION installed and healthy."
echo "LAN: http://$(hostname -I | awk '{print $1}'):$HOST_PORT"
echo "Proxy upstream: http://rogueforge:7810"
