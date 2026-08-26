#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DEFAULT_TEST_BRANCH="v0.8.5-runtime-fixes"
MODE=${1:-latest}
BRANCH=""

if [[ $MODE == branch ]]; then
  BRANCH=${2:-}
  [[ -n $BRANCH && $BRANCH =~ ^[A-Za-z0-9._/-]+$ ]] || { echo "Usage: ./update.sh branch <branch-name>" >&2; exit 2; }
  TARGET="branch:$BRANCH"
elif [[ $MODE == testing ]]; then
  BRANCH=${ROGUEFORGE_TEST_BRANCH:-$DEFAULT_TEST_BRANCH}
  TARGET="testing"
else
  TARGET=$MODE
  [[ $TARGET == v* ]] && TARGET=${TARGET#v}
  [[ $TARGET =~ ^([0-9]+\.[0-9]+\.[0-9]+|latest|main)$ ]] || { echo "Usage: ./update.sh [latest|main|testing|X.Y.Z] | ./update.sh branch <branch-name>" >&2; exit 2; }
fi

[[ $EUID -ne 0 ]] || { echo "Run as the container owner, not root/sudo." >&2; exit 1; }
for cmd in curl awk; do command -v "$cmd" >/dev/null || { echo "Missing runtime: $cmd" >&2; exit 2; }; done
cd "$INSTALL_DIR"
[[ -f compose.yaml && -f .env && -f data/auth.json ]] || { echo "Incomplete RogueForge installation at $INSTALL_DIR" >&2; exit 2; }

REF=main
IMAGE_TAG=latest
CHANNEL=production
if [[ $TARGET =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  IMAGE_TAG="$TARGET"
elif [[ $TARGET == testing || $TARGET == branch:* ]]; then
  REF="$BRANCH"
  CHANNEL=testing
  if [[ $TARGET == testing ]]; then
    IMAGE_TAG=testing
  else
    SAFE_BRANCH=$(printf '%s' "$BRANCH" | tr '/_' '--' | tr -cd '[:alnum:].-')
    IMAGE_TAG="branch-$SAFE_BRANCH"
  fi
fi
BASE="https://raw.githubusercontent.com/RogueAssassin/RogueForge/$REF"

# All RogueForge deployment backups live outside the stacks root.
BACKUP_ROOT=${ROGUEFORGE_BACKUP_TMP:-${TMPDIR:-/tmp}/rogueforge/update-backups}
mkdir -p "$BACKUP_ROOT"

# Migrate updater backups created by older releases out of the installation tree.
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
[[ -f update-testing.sh ]] && cp -a update-testing.sh "$BACKUP/"

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
echo "Channel: $CHANNEL"
echo "Source ref: $REF"
echo "Deployment runtime: $deploy_engine"
echo "Image tag: $IMAGE_TAG"
echo "Backup: $BACKUP"

# Validate branch/source exists before replacing local deployment files.
if ! curl -fsSL "$BASE/compose.yaml" -o "$BACKUP/compose.download"; then
  echo "RogueForge source ref '$REF' is unavailable on GitHub." >&2
  exit 3
fi
if ! curl -fsSL "$BASE/update.sh" -o "$BACKUP/update.download"; then
  echo "RogueForge updater is unavailable on source ref '$REF'." >&2
  exit 3
fi
install -m 0644 "$BACKUP/compose.download" "$INSTALL_DIR/compose.yaml"
install -m 0755 "$BACKUP/update.download" "$INSTALL_DIR/update.sh"

# Preserve local settings while switching only image/channel metadata.
if grep -q '^ROGUEFORGE_IMAGE=' .env; then
  sed -i "s#^ROGUEFORGE_IMAGE=.*#ROGUEFORGE_IMAGE=ghcr.io/rogueassassin/rogueforge:$IMAGE_TAG#" .env
else
  printf '\nROGUEFORGE_IMAGE=ghcr.io/rogueassassin/rogueforge:%s\n' "$IMAGE_TAG" >> .env
fi
if grep -q '^ROGUEFORGE_CHANNEL=' .env; then
  sed -i "s#^ROGUEFORGE_CHANNEL=.*#ROGUEFORGE_CHANNEL=$CHANNEL#" .env
else
  printf 'ROGUEFORGE_CHANNEL=%s\n' "$CHANNEL" >> .env
fi

if ! $deploy_engine pull "ghcr.io/rogueassassin/rogueforge:$IMAGE_TAG"; then
  echo "RogueForge image tag '$IMAGE_TAG' is not published in GHCR." >&2
  if [[ $CHANNEL == testing ]]; then
    echo "Wait for the testing-branch GitHub Actions build to finish, then retry." >&2
  else
    echo "Use './update.sh latest' for current production or choose a published version." >&2
  fi
  exit 4
fi
$compose_bin -f compose.yaml up -d --remove-orphans

HEALTH_FILE="${TMPDIR:-/tmp}/rogueforge-health.$$"
trap 'rm -f "$HEALTH_FILE"' EXIT
for _ in {1..30}; do
  if curl -fsS "http://127.0.0.1:${ROGUEFORGE_HOST_PORT:-17810}/health" >"$HEALTH_FILE" 2>/dev/null; then
    echo; cat "$HEALTH_FILE"; echo
    echo "RogueForge $CHANNEL update complete."
    [[ $CHANNEL == testing ]] && echo "TESTING BUILD ACTIVE: $REF ($IMAGE_TAG)"
    exit 0
  fi
  sleep 2
done

echo "Health check failed. Deployment backup remains at $BACKUP" >&2
$compose_bin -f compose.yaml ps >&2 || true
$deploy_engine logs --tail 100 rogueforge >&2 || true
exit 1
