#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VERSION=${1:-latest}
[[ $VERSION == v* ]] && VERSION=${VERSION#v}
IMAGE=${ROGUEFORGE_IMAGE_OVERRIDE:-ghcr.io/rogueassassin/rogueforge:$VERSION}

if [[ $EUID -eq 0 ]]; then
  echo "Run as the container owner, not with sudo." >&2
  exit 1
fi
for command in curl awk; do
  command -v "$command" >/dev/null || { echo "Missing required command: $command" >&2; exit 2; }
done
[[ $VERSION =~ ^([0-9]+\.[0-9]+\.[0-9]+|sha-[0-9a-f]+|latest)$ ]] || {
  echo "Use a semantic version, sha-<commit>, or latest." >&2
  exit 2
}
[[ -f $INSTALL_DIR/compose.yaml && -f $INSTALL_DIR/.env ]] || {
  echo "This script must be stored in the RogueForge deployment folder." >&2
  exit 2
}

cd "$INSTALL_DIR"
deploy_engine=$(awk -F= '$1 == "ROGUEFORGE_DEPLOY_ENGINE" {print $2}' .env | tail -n 1)
if [[ -z $deploy_engine ]]; then
  grep -q 'podman.sock' .env && deploy_engine=podman || deploy_engine=docker
fi
if [[ $deploy_engine == podman ]]; then
  ENGINE=(podman)
  COMPOSE=(podman-compose)
else
  ENGINE=(docker)
  if docker compose version >/dev/null 2>&1; then COMPOSE=(docker compose); else COMPOSE=(docker-compose); fi
fi
command -v "${ENGINE[0]}" >/dev/null || { echo "Missing runtime: ${ENGINE[0]}" >&2; exit 2; }
command -v "${COMPOSE[0]}" >/dev/null || { echo "Missing Compose command: ${COMPOSE[0]}" >&2; exit 2; }

old_image=$(awk -F= '$1 == "ROGUEFORGE_IMAGE" {print substr($0, index($0, "=") + 1)}' .env | tail -n 1)
old_image=${old_image:-ghcr.io/rogueassassin/rogueforge:0.4.1}
host_port=$(awk -F= '$1 == "ROGUEFORGE_HOST_PORT" {print $2}' .env | tail -n 1)
host_port=${host_port:-17810}
timestamp=$(date +%Y%m%d%H%M%S)
backup=".env.backup-$timestamp"

echo "Preflight: pulling $IMAGE with $deploy_engine..."
"${ENGINE[@]}" pull "$IMAGE"
cp -a .env "$backup"

rollback() {
  status=$?
  echo "Upgrade failed; restoring $old_image" >&2
  cp -a "$backup" .env
  "${COMPOSE[@]}" up -d >/dev/null 2>&1 || true
  exit "$status"
}
trap rollback ERR

if grep -q '^ROGUEFORGE_IMAGE=' .env; then
  sed -i "s|^ROGUEFORGE_IMAGE=.*|ROGUEFORGE_IMAGE=$IMAGE|" .env
else
  printf '\nROGUEFORGE_IMAGE=%s\n' "$IMAGE" >> .env
fi

"${COMPOSE[@]}" pull
"${COMPOSE[@]}" up -d --force-recreate
curl --fail --silent --show-error --retry 15 --retry-delay 2 --retry-all-errors "http://127.0.0.1:$host_port/health" >/dev/null

trap - ERR
echo "RogueForge upgraded successfully."
echo "  Runtime:        $deploy_engine"
echo "  Previous image: $old_image"
echo "  Current image:  $IMAGE"
echo "  Environment:    $backup"
