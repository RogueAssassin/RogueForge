#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TARGET=${1:-latest}
[[ $TARGET == v* ]] && TARGET=${TARGET#v}
[[ $TARGET =~ ^([0-9]+\.[0-9]+\.[0-9]+|latest|main)$ ]] || { echo "Usage: ./update.sh [latest|main|X.Y.Z]" >&2; exit 2; }
[[ $EUID -ne 0 ]] || { echo "Run as the container owner, not root/sudo." >&2; exit 1; }
for cmd in curl awk; do command -v "$cmd" >/dev/null || { echo "Missing runtime: $cmd" >&2; exit 2; }; done
cd "$INSTALL_DIR"
[[ -f compose.yaml && -f .env && -f data/auth.json ]] || { echo "Incomplete RogueForge installation at $INSTALL_DIR" >&2; exit 2; }

REF=main
IMAGE_TAG=latest
if [[ $TARGET =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then REF="v$TARGET"; IMAGE_TAG="$TARGET"; fi
BASE="https://raw.githubusercontent.com/RogueAssassin/RogueForge/$REF"

# Update backups are deliberately kept outside ROGUEFORGE_STACKS_DIR so recursive
# Compose discovery never mistakes a historical deployment snapshot for a stack.
BACKUP_ROOT=${ROGUEFORGE_BACKUP_TMP:-${TMPDIR:-/tmp}/rogueforge-update-backups}
mkdir -p "$BACKUP_ROOT"

# Migrate backups created by pre-0.8.2 updater revisions out of the installation tree.
LEGACY_BACKUPS="$INSTALL_DIR/data/update-backups"
if [[ -d "$LEGACY_BACKUPS" ]]; then
  LEGACY_TARGET="$BACKUP_ROOT/legacy-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$LEGACY_TARGET"
  shopt -s nullglob dotglob
  legacy_items=("$LEGACY_BACKUPS"/*)
  if ((${#legacy_items[@]})); then mv "${legacy_items[@]}" "$LEGACY_TARGET/"; fi
  shopt -u nullglob dotglob
  rmdir "$LEGACY_BACKUPS" 2>/dev/null || true
fi

BACKUP="$BACKUP_ROOT/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
cp -a compose.yaml .env "$BACKUP/"
[[ -f update.sh ]] && cp -a update.sh "$BACKUP/"

deploy_engine=$(awk -F= '$1=="ROGUEFORGE_DEPLOY_ENGINE"{print $2}' .env | tail -n1 | tr -d '\r ' || true)
if [[ $deploy_engine != podman && $deploy_engine != docker ]]; then
  if command -v podman >/dev/null && podman info >/dev/null 2>&1; then deploy_engine=podman
  elif command -v docker >/dev/null && docker info >/dev/null 2>&1; then deploy_engine=docker
  else echo "Unable to detect a working Podman or Docker runtime." >&2; exit 2; fi
fi
compose_bin=podman-compose
[[ $deploy_engine == docker ]] && compose_bin=docker-compose
command -v "$compose_bin" >/dev/null || { echo "Missing runtime: $compose_bin" >&2; exit 2; }

echo "RogueForge update target: $TARGET"
echo "Deployment runtime: $deploy_engine"
echo "Backup: $BACKUP"

# Verify release/source exists before replacing local deployment files.
if ! curl -fsSI "$BASE/compose.yaml" >/dev/null; then
  echo "RogueForge source '$REF' is not published on GitHub." >&2
  [[ $TARGET =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] && echo "Use './update.sh main' to test unreleased main, or './update.sh latest' for the latest published build." >&2
  exit 3
fi

for file in compose.yaml update.sh; do
  tmp=$(mktemp)
  curl -fsSL "$BASE/$file" -o "$tmp"
  install -m $([[ $file == *.sh ]] && echo 0755 || echo 0644) "$tmp" "$INSTALL_DIR/$file"
  rm -f "$tmp"
done

# Preserve local settings while changing only the image requested for this update.
if grep -q '^ROGUEFORGE_IMAGE=' .env; then
  sed -i "s#^ROGUEFORGE_IMAGE=.*#ROGUEFORGE_IMAGE=ghcr.io/rogueassassin/rogueforge:$IMAGE_TAG#" .env
else
  printf '\nROGUEFORGE_IMAGE=ghcr.io/rogueassassin/rogueforge:%s\n' "$IMAGE_TAG" >> .env
fi

$deploy_engine pull "ghcr.io/rogueassassin/rogueforge:$IMAGE_TAG"
$compose_bin -f compose.yaml up -d --remove-orphans

for _ in {1..30}; do
  if curl -fsS "http://127.0.0.1:${ROGUEFORGE_HOST_PORT:-17810}/health" >/tmp/rogueforge-health.$$ 2>/dev/null; then
    echo; cat /tmp/rogueforge-health.$$; echo; rm -f /tmp/rogueforge-health.$$
    echo "RogueForge update complete."
    exit 0
  fi
  sleep 2
done

echo "Health check failed. Deployment backup remains at $BACKUP" >&2
$compose_bin -f compose.yaml ps >&2 || true
$deploy_engine logs --tail 100 rogueforge >&2 || true
exit 1
