#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VERSION=${1:-latest}
[[ $VERSION == v* ]] && VERSION=${VERSION#v}
[[ $VERSION =~ ^([0-9]+\.[0-9]+\.[0-9]+|latest)$ ]] || { echo "Use a semantic version or latest." >&2; exit 2; }
IMAGE=${ROGUEFORGE_IMAGE_OVERRIDE:-ghcr.io/rogueassassin/rogueforge:$VERSION}
RELEASE_REF=$VERSION
[[ $VERSION == latest ]] && RELEASE_REF=main || RELEASE_REF=v$VERSION
BASE_URL="https://raw.githubusercontent.com/RogueAssassin/RogueForge/$RELEASE_REF"

[[ $EUID -ne 0 ]] || { echo "Run as the container owner, not sudo/root." >&2; exit 1; }
for command in curl awk; do command -v "$command" >/dev/null || { echo "Missing: $command" >&2; exit 2; }; done
[[ -f $INSTALL_DIR/compose.yaml && -f $INSTALL_DIR/.env && -f $INSTALL_DIR/data/auth.json ]] || { echo "Incomplete RogueForge installation at $INSTALL_DIR" >&2; exit 2; }

cd "$INSTALL_DIR"

# Normalize any CRLF/whitespace in older .env files before deciding which runtime owns the deployment.
deploy_engine=$(awk -F= '$1 == "ROGUEFORGE_DEPLOY_ENGINE" {print $2}' .env | tail -n1 | tr -d '\r' | xargs 2>/dev/null || true)
engine_hint=$(awk -F= '$1 == "ROGUEFORGE_ENGINE" {print $2}' .env | tail -n1 | tr -d '\r' | xargs 2>/dev/null || true)
socket_source=$(awk -F= '$1 == "ROGUEFORGE_SOCKET_SOURCE" {print substr($0,index($0,"=")+1)}' .env | tail -n1 | tr -d '\r' | xargs 2>/dev/null || true)

if [[ $deploy_engine != podman && $deploy_engine != docker ]]; then
  deploy_engine=$engine_hint
fi
if [[ $deploy_engine != podman && $deploy_engine != docker ]]; then
  if [[ $socket_source == *podman.sock* ]] || grep -q 'podman.sock' .env; then
    deploy_engine=podman
  elif [[ $socket_source == *docker.sock* ]] || grep -q 'docker.sock' .env; then
    deploy_engine=docker
  fi
fi
# Final runtime probe: prefer the working rootless Podman store when available.
if [[ $deploy_engine != podman && $deploy_engine != docker ]]; then
  if command -v podman >/dev/null && podman info >/dev/null 2>&1; then
    deploy_engine=podman
  elif command -v docker >/dev/null && docker info >/dev/null 2>&1; then
    deploy_engine=docker
  else
    echo "Unable to determine the deployment runtime from .env or the current user session." >&2
    exit 2
  fi
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

echo "Detected deployment runtime: $deploy_engine"

old_image=$(awk -F= '$1 == "ROGUEFORGE_IMAGE" {print substr($0,index($0,"=")+1)}' .env | tail -n1 | tr -d '\r')
host_port=$(awk -F= '$1 == "ROGUEFORGE_HOST_PORT" {print $2}' .env | tail -n1 | tr -d '\r'); host_port=${host_port:-17810}
timestamp=$(date +%Y%m%d%H%M%S)
backup_dir="$INSTALL_DIR/backup-$timestamp"
mkdir -p "$backup_dir"
cp -a .env compose.yaml setup-auth.py upgrade.sh data/auth.json "$backup_dir/"

rollback() {
  status=$?
  echo "Upgrade failed; restoring deployment backup $backup_dir" >&2
  cp -a "$backup_dir/.env" .env || true
  cp -a "$backup_dir/compose.yaml" compose.yaml || true
  cp -a "$backup_dir/setup-auth.py" setup-auth.py || true
  cp -a "$backup_dir/upgrade.sh" upgrade.sh || true
  "${COMPOSE[@]}" up -d >/dev/null 2>&1 || true
  exit "$status"
}
trap rollback ERR

echo "Preflight: pulling $IMAGE with $deploy_engine..."
"${ENGINE[@]}" pull "$IMAGE"

# Keep host-specific .env and auth data, but upgrade the deployment definition and helpers.
for file in compose.yaml setup-auth.py .env.example upgrade.sh; do
  tmp="$file.new"
  curl --fail --silent --show-error --location "$BASE_URL/$file" -o "$tmp"
  [[ -s $tmp ]] || { echo "Downloaded empty $file" >&2; exit 2; }
done
mv compose.yaml.new compose.yaml
mv setup-auth.py.new setup-auth.py
mv .env.example.new .env.example
mv upgrade.sh.new upgrade.sh
chmod 755 upgrade.sh

# Normalize the recorded deployment runtime so future upgrades cannot fall through to Docker.
if grep -q '^ROGUEFORGE_DEPLOY_ENGINE=' .env; then
  sed -i "s|^ROGUEFORGE_DEPLOY_ENGINE=.*|ROGUEFORGE_DEPLOY_ENGINE=$deploy_engine|" .env
else
  printf '\nROGUEFORGE_DEPLOY_ENGINE=%s\n' "$deploy_engine" >> .env
fi
if grep -q '^ROGUEFORGE_ENGINE=' .env; then
  sed -i "s|^ROGUEFORGE_ENGINE=.*|ROGUEFORGE_ENGINE=$deploy_engine|" .env
else
  printf 'ROGUEFORGE_ENGINE=%s\n' "$deploy_engine" >> .env
fi
if grep -q '^ROGUEFORGE_IMAGE=' .env; then sed -i "s|^ROGUEFORGE_IMAGE=.*|ROGUEFORGE_IMAGE=$IMAGE|" .env; else printf 'ROGUEFORGE_IMAGE=%s\n' "$IMAGE" >> .env; fi
if ! grep -q '^ROGUEFORGE_SELF_STACK=' .env; then printf 'ROGUEFORGE_SELF_STACK=rogueforge\n' >> .env; fi

"${COMPOSE[@]}" config >/dev/null
"${COMPOSE[@]}" pull
"${COMPOSE[@]}" up -d --force-recreate
curl --fail --silent --show-error --retry 20 --retry-delay 2 --retry-all-errors "http://127.0.0.1:$host_port/health" >/dev/null
trap - ERR

echo "RogueForge upgraded successfully."
echo "Runtime:        $deploy_engine"
echo "Previous image: ${old_image:-unknown}"
echo "Current image:  $IMAGE"
echo "Backup:         $backup_dir"
