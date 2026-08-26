#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DEFAULT_TEST_BRANCH="v0.8.6-testing"
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

REF=main; IMAGE_TAG=latest; CHANNEL=production
if [[ $TARGET =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then IMAGE_TAG="$TARGET"
elif [[ $TARGET == testing || $TARGET == branch:* ]]; then
  REF="$BRANCH"; CHANNEL=testing
  if [[ $TARGET == testing ]]; then IMAGE_TAG=testing
  else SAFE_BRANCH=$(printf '%s' "$BRANCH" | tr '/_' '--' | tr -cd '[:alnum:].-'); IMAGE_TAG="branch-$SAFE_BRANCH"; fi
fi
BASE="https://raw.githubusercontent.com/RogueAssassin/RogueForge/$REF"

BACKUP_ROOT=${ROGUEFORGE_BACKUP_TMP:-${TMPDIR:-/tmp}/rogueforge/update-backups}; mkdir -p "$BACKUP_ROOT"
LEGACY_BACKUPS="$INSTALL_DIR/data/update-backups"
if [[ -d "$LEGACY_BACKUPS" ]]; then
  LEGACY_TARGET="$BACKUP_ROOT/legacy-$(date +%Y%m%d-%H%M%S)"; mkdir -p "$LEGACY_TARGET"
  shopt -s nullglob dotglob; legacy_items=("$LEGACY_BACKUPS"/*); ((${#legacy_items[@]})) && mv "${legacy_items[@]}" "$LEGACY_TARGET/"; shopt -u nullglob dotglob
  rmdir "$LEGACY_BACKUPS" 2>/dev/null || true
fi
BACKUP="$BACKUP_ROOT/$(date +%Y%m%d-%H%M%S)"; mkdir -p "$BACKUP"; cp -a compose.yaml .env "$BACKUP/"
[[ -f update.sh ]] && cp -a update.sh "$BACKUP/"; [[ -f update-testing.sh ]] && cp -a update-testing.sh "$BACKUP/"

deploy_engine=$(awk -F= '$1=="ROGUEFORGE_DEPLOY_ENGINE"{print $2}' .env | tail -n1 | tr -d '\r ' || true)
if [[ $deploy_engine != podman && $deploy_engine != docker ]]; then
  if command -v podman >/dev/null && podman info >/dev/null 2>&1; then deploy_engine=podman
  elif command -v docker >/dev/null && docker info >/dev/null 2>&1; then deploy_engine=docker
  else echo "Unable to detect a working Podman or Docker runtime." >&2; exit 2; fi
fi

if [[ $deploy_engine == podman ]]; then
  command -v podman >/dev/null || { echo "Missing runtime: podman" >&2; exit 2; }
  podman compose version >/dev/null 2>&1 || { echo "Podman Compose provider is unavailable." >&2; exit 2; }
  compose_cmd=(podman compose --env-file "$INSTALL_DIR/.env" -f "$INSTALL_DIR/compose.yaml")
else
  command -v docker >/dev/null || { echo "Missing runtime: docker" >&2; exit 2; }
  if docker compose version >/dev/null 2>&1; then compose_cmd=(docker compose --env-file "$INSTALL_DIR/.env" -f "$INSTALL_DIR/compose.yaml")
  elif command -v docker-compose >/dev/null; then compose_cmd=(docker-compose --env-file "$INSTALL_DIR/.env" -f "$INSTALL_DIR/compose.yaml")
  else echo "Docker Compose provider is unavailable." >&2; exit 2; fi
fi

echo "RogueForge update target: $TARGET"
echo "Channel: $CHANNEL"
echo "Source ref: $REF"
echo "Deployment runtime: $deploy_engine"
echo "Image tag: $IMAGE_TAG"
echo "Backup: $BACKUP"

curl -fsSL "$BASE/compose.yaml" -o "$BACKUP/compose.download" || { echo "RogueForge source ref '$REF' is unavailable." >&2; exit 3; }
curl -fsSL "$BASE/update.sh" -o "$BACKUP/update.download" || { echo "RogueForge updater is unavailable on '$REF'." >&2; exit 3; }
install -m 0644 "$BACKUP/compose.download" "$INSTALL_DIR/compose.yaml"; install -m 0755 "$BACKUP/update.download" "$INSTALL_DIR/update.sh"

set_env(){ local key=$1 value=$2; if grep -q "^${key}=" .env; then sed -i "s#^${key}=.*#${key}=${value}#" .env; else printf '%s=%s\n' "$key" "$value" >> .env; fi; }
set_env ROGUEFORGE_IMAGE "ghcr.io/rogueassassin/rogueforge:$IMAGE_TAG"
set_env ROGUEFORGE_CHANNEL "$CHANNEL"

MEDIA_ROOT=$(awk -F= '$1=="ROGUEFORGE_MEDIA_ROOT"{print substr($0,index($0,"=")+1)}' .env | tail -n1 | tr -d '\r' || true); [[ -n $MEDIA_ROOT ]] || MEDIA_ROOT=/opt/media-server
COMPOSE_ROOT=$(awk -F= '$1=="ROGUEFORGE_COMPOSE_ROOT"{print substr($0,index($0,"=")+1)}' .env | tail -n1 | tr -d '\r' || true)
LEGACY_STACKS=$(awk -F= '$1=="ROGUEFORGE_STACKS_DIR"{print substr($0,index($0,"=")+1)}' .env | tail -n1 | tr -d '\r' || true)
if [[ -z $COMPOSE_ROOT ]]; then
  if [[ ${LEGACY_STACKS:-} == /opt/media-server && -d /opt/media-server/compose ]]; then COMPOSE_ROOT=/opt/media-server/compose
  elif [[ -n ${LEGACY_STACKS:-} ]]; then COMPOSE_ROOT=$LEGACY_STACKS
  elif [[ -d "$MEDIA_ROOT/compose" ]]; then COMPOSE_ROOT="$MEDIA_ROOT/compose"
  else COMPOSE_ROOT=$MEDIA_ROOT; fi
fi
ENV_ROOT=$(awk -F= '$1=="ROGUEFORGE_ENV_ROOT"{print substr($0,index($0,"=")+1)}' .env | tail -n1 | tr -d '\r' || true); [[ -n $ENV_ROOT ]] || ENV_ROOT=$COMPOSE_ROOT
set_env ROGUEFORGE_MEDIA_ROOT "$MEDIA_ROOT"
set_env ROGUEFORGE_COMPOSE_ROOT "$COMPOSE_ROOT"
set_env ROGUEFORGE_ENV_ROOT "$ENV_ROOT"
set_env ROGUEFORGE_STACKS_DIR "$COMPOSE_ROOT"

echo "Media root:   $MEDIA_ROOT"
echo "Compose root: $COMPOSE_ROOT"
echo "Env root:     $ENV_ROOT"
[[ -d "$MEDIA_ROOT" ]] || { echo "Media root does not exist: $MEDIA_ROOT" >&2; exit 3; }
[[ -d "$COMPOSE_ROOT" ]] || { echo "Compose root does not exist: $COMPOSE_ROOT" >&2; exit 3; }
[[ -d "$ENV_ROOT" ]] || { echo "Env root does not exist: $ENV_ROOT" >&2; exit 3; }

$deploy_engine pull "ghcr.io/rogueassassin/rogueforge:$IMAGE_TAG" || { echo "RogueForge image tag '$IMAGE_TAG' is not published in GHCR." >&2; exit 4; }
"${compose_cmd[@]}" up -d --remove-orphans --pull never

HEALTH_FILE="${TMPDIR:-/tmp}/rogueforge-health.$$"; trap 'rm -f "$HEALTH_FILE"' EXIT
for _ in {1..30}; do
  if curl -fsS "http://127.0.0.1:${ROGUEFORGE_HOST_PORT:-17810}/health" >"$HEALTH_FILE" 2>/dev/null; then
    echo; cat "$HEALTH_FILE"; echo
    echo "RogueForge $CHANNEL update complete."
    echo "Media root:   $MEDIA_ROOT"
    echo "Compose root: $COMPOSE_ROOT"
    echo "Env root:     $ENV_ROOT"
    [[ $CHANNEL == testing ]] && echo "TESTING BUILD ACTIVE: $REF ($IMAGE_TAG)"
    exit 0
  fi
  sleep 2
done

echo "Health check failed. Deployment backup remains at $BACKUP" >&2
"${compose_cmd[@]}" ps >&2 || true; $deploy_engine logs --tail 100 rogueforge >&2 || true
exit 1
