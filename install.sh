#!/usr/bin/env bash
set -Eeuo pipefail
VERSION=2.1.0
INSTALL_DIR=${ROGUEFORGE_INSTALL_DIR:-/opt/media-server/rogueforge}
MEDIA_ROOT=${ROGUEFORGE_MEDIA_ROOT:-/opt/media-server}
COMPOSE_ROOT=${ROGUEFORGE_COMPOSE_ROOT:-${ROGUEFORGE_STACKS_DIR:-$MEDIA_ROOT}}
ENV_ROOT=${ROGUEFORGE_ENV_ROOT:-$COMPOSE_ROOT}
HOST_PORT=${ROGUEFORGE_HOST_PORT:-17810}
PUBLIC_URL=${ROGUEFORGE_PUBLIC_URL:-https://manage.roguegaming.com.au}
NETWORK=${ROGUEFORGE_NETWORK:-media-net}
USERNAME=${ROGUEFORGE_ADMIN_USERNAME:-administrator}
ENGINE=${ROGUEFORGE_DEPLOY_ENGINE:-auto}
[[ $EUID -ne 0 ]] || { echo "Run as the account that owns the containers, not root/sudo." >&2; exit 1; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --engine) ENGINE=$2; shift 2;;
    --install-dir) INSTALL_DIR=$2; shift 2;;
    --media-root) MEDIA_ROOT=$2; shift 2;;
    --compose-root|--stacks-dir) COMPOSE_ROOT=$2; shift 2;;
    --env-root) ENV_ROOT=$2; shift 2;;
    --host-port) HOST_PORT=$2; shift 2;;
    --public-url) PUBLIC_URL=$2; shift 2;;
    --network) NETWORK=$2; shift 2;;
    --username) USERNAME=$2; shift 2;;
    --yes) shift;;
    *) echo "Unknown option: $1" >&2; exit 2;;
  esac
done
for c in curl python3; do command -v "$c" >/dev/null || { echo "Missing: $c" >&2; exit 2; }; done
if [[ $ENGINE == auto ]]; then
  if command -v podman >/dev/null && podman info >/dev/null 2>&1; then ENGINE=podman
  elif command -v docker >/dev/null && docker info >/dev/null 2>&1; then ENGINE=docker
  else echo "No working Podman or Docker runtime found." >&2; exit 2; fi
fi
[[ $ENGINE == podman || $ENGINE == docker ]] || { echo "--engine must be podman or docker" >&2; exit 2; }
[[ -d "$MEDIA_ROOT" ]] || { echo "Media root does not exist: $MEDIA_ROOT" >&2; exit 2; }
[[ -d "$COMPOSE_ROOT" ]] || { echo "Compose root does not exist: $COMPOSE_ROOT" >&2; exit 2; }
[[ -d "$ENV_ROOT" ]] || { echo "Env root does not exist: $ENV_ROOT" >&2; exit 2; }
mkdir -p "$INSTALL_DIR/data"; cd "$INSTALL_DIR"
if [[ $VERSION == *-* ]]; then DEFAULT_SOURCE_REF=testing; else DEFAULT_SOURCE_REF=main; fi
SOURCE_REF=${ROGUEFORGE_SOURCE_REF:-$DEFAULT_SOURCE_REF}
BASE="https://raw.githubusercontent.com/RogueAssassin/RogueForge/$SOURCE_REF"
for f in compose.yaml update.sh setup-auth.py .env.example; do curl -fsSL "$BASE/$f" -o "$f"; done
chmod +x update.sh setup-auth.py

# Fresh installs inherit the full administrator-reference .env, including comments.
# Existing .env files are never replaced; only required machine-specific values are updated.
if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
fi
set_env(){
  local key=$1 value=$2
  if grep -q "^${key}=" .env; then
    sed -i "s#^${key}=.*#${key}=${value}#" .env
  else
    printf '\n%s=%s\n' "$key" "$value" >> .env
  fi
}

set_env ROGUEFORGE_INSTALL_DIR "$INSTALL_DIR"
set_env ROGUEFORGE_DATA_DIR "$INSTALL_DIR/data"
set_env ROGUEFORGE_HOST_PORT "$HOST_PORT"
set_env ROGUEFORGE_IMAGE "ghcr.io/rogueassassin/rogueforge:$VERSION"
set_env ROGUEFORGE_DEPLOY_ENGINE "$ENGINE"
set_env ROGUEFORGE_ENGINE "$ENGINE"
set_env ROGUEFORGE_MEDIA_ROOT "$MEDIA_ROOT"
set_env ROGUEFORGE_COMPOSE_ROOT "$COMPOSE_ROOT"
set_env ROGUEFORGE_ENV_ROOT "$ENV_ROOT"
set_env ROGUEFORGE_STACKS_DIR "$COMPOSE_ROOT"
set_env ROGUEFORGE_ICONS_DIR "$MEDIA_ROOT/roguedashboard/app/static/icons"
set_env ROGUEFORGE_SELF_STACK "rogueforge"
set_env ROGUEFORGE_PUBLIC_URL "$PUBLIC_URL"
set_env ROGUEFORGE_NETWORK "$NETWORK"
set_env ROGUEFORGE_AUTH_FILE "/opt/rogueforge/data/auth.json"
set_env ROGUEFORGE_OPERATIONS_FILE "/opt/rogueforge/data/operations.json"

if [[ $ENGINE == podman ]]; then
  uid=$(id -u); sock="/run/user/$uid/podman/podman.sock"; systemctl --user enable --now podman.socket >/dev/null 2>&1 || true
  [[ -S $sock ]] || { echo "Rootless Podman socket not found: $sock" >&2; exit 2; }
  podman compose version >/dev/null 2>&1 || { echo "Podman Compose provider unavailable" >&2; exit 2; }
  set_env ROGUEFORGE_SOCKET_SOURCE "$sock"
  set_env ROGUEFORGE_SOCKET_TARGET "/run/podman/podman.sock"
  set_env ROGUEFORGE_CONTAINER_HOST "unix:///run/podman/podman.sock"
  set_env ROGUEFORGE_PODMAN_REMOTE "true"
  compose_cmd=(podman compose --env-file "$INSTALL_DIR/.env" -f "$INSTALL_DIR/compose.yaml")
else
  set_env ROGUEFORGE_SOCKET_SOURCE "/var/run/docker.sock"
  set_env ROGUEFORGE_SOCKET_TARGET "/var/run/docker.sock"
  set_env ROGUEFORGE_CONTAINER_HOST "unix:///var/run/docker.sock"
  set_env ROGUEFORGE_PODMAN_REMOTE "false"
  if docker compose version >/dev/null 2>&1; then compose_cmd=(docker compose --env-file "$INSTALL_DIR/.env" -f "$INSTALL_DIR/compose.yaml"); else compose_cmd=(docker-compose --env-file "$INSTALL_DIR/.env" -f "$INSTALL_DIR/compose.yaml"); fi
fi
if ! $ENGINE network exists "$NETWORK" >/dev/null 2>&1; then $ENGINE network create "$NETWORK" >/dev/null; fi
if [[ ! -f data/auth.json ]]; then python3 setup-auth.py --username "$USERNAME"; fi
$ENGINE pull "ghcr.io/rogueassassin/rogueforge:$VERSION"
"${compose_cmd[@]}" up -d --remove-orphans
for _ in {1..30}; do curl -fsS "http://127.0.0.1:$HOST_PORT/health" && { echo; echo "RogueForge $VERSION installed at $INSTALL_DIR"; exit 0; }; sleep 2; done
echo "RogueForge did not pass its health check." >&2; $ENGINE logs --tail 100 rogueforge >&2 || true; exit 1
