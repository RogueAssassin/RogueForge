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
deploy_engine=$(awk -F= '$1 == "ROGUEFORGE_DEPLOY_ENGINE" {print $2}' .env | tail -n1)
[[ -n $deploy_engine ]] || { grep -q 'podman.sock' .env && deploy_engine=podman || deploy_engine=docker; }
if [[ $deploy_engine == podman ]]; then ENGINE=(podman); COMPOSE=(podman-compose); else ENGINE=(docker); docker compose version >/dev/null 2>&1 && COMPOSE=(docker compose) || COMPOSE=(docker-compose); fi
command -v "${ENGINE[0]}" >/dev/null || { echo "Missing runtime: ${ENGINE[0]}" >&2; exit 2; }
command -v "${COMPOSE[0]}" >/dev/null || { echo "Missing Compose command: ${COMPOSE[0]}" >&2; exit 2; }

old_image=$(awk -F= '$1 == "ROGUEFORGE_IMAGE" {print substr($0,index($0,"=")+1)}' .env | tail -n1)
host_port=$(awk -F= '$1 == "ROGUEFORGE_HOST_PORT" {print $2}' .env | tail -n1); host_port=${host_port:-17810}
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

if grep -q '^ROGUEFORGE_IMAGE=' .env; then sed -i "s|^ROGUEFORGE_IMAGE=.*|ROGUEFORGE_IMAGE=$IMAGE|" .env; else printf '\nROGUEFORGE_IMAGE=%s\n' "$IMAGE" >> .env; fi
if ! grep -q '^ROGUEFORGE_SELF_STACK=' .env; then printf 'ROGUEFORGE_SELF_STACK=rogueforge\n' >> .env; fi

"${COMPOSE[@]}" config >/dev/null
"${COMPOSE[@]}" pull
"${COMPOSE[@]}" up -d --force-recreate
curl --fail --silent --show-error --retry 20 --retry-delay 2 --retry-all-errors "http://127.0.0.1:$host_port/health" >/dev/null
trap - ERR

echo "RogueForge upgraded successfully."
echo "Previous image: ${old_image:-unknown}"
echo "Current image:  $IMAGE"
echo "Backup:         $backup_dir"
