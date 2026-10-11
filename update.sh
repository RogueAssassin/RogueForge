#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DEFAULT_TEST_BRANCH="testing"
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
  [[ $TARGET =~ ^([0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.]+)?|latest|main)$ ]] || { echo "Usage: ./update.sh [latest|main|testing|X.Y.Z|X.Y.Z-rcN] | ./update.sh branch <branch-name>" >&2; exit 2; }
fi

[[ $EUID -ne 0 ]] || { echo "Run as the container owner, not root/sudo." >&2; exit 1; }
for cmd in curl awk; do command -v "$cmd" >/dev/null || { echo "Missing runtime: $cmd" >&2; exit 2; }; done
cd "$INSTALL_DIR"
[[ -f compose.yaml && -f .env && -f data/auth.json ]] || { echo "Incomplete RogueForge installation at $INSTALL_DIR" >&2; exit 2; }

# Only one update at a time.
if command -v flock >/dev/null; then
  exec 9>"$INSTALL_DIR/.update.lock"
  flock -n 9 || { echo "Another RogueForge update is already running." >&2; exit 1; }
fi

REF=main; IMAGE_TAG=latest; CHANNEL=production
if [[ $TARGET =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.]+)?$ ]]; then IMAGE_TAG="$TARGET"
elif [[ $TARGET == testing || $TARGET == branch:* ]]; then
  REF="$BRANCH"; CHANNEL=testing
  if [[ $TARGET == testing ]]; then IMAGE_TAG=testing
  else SAFE_BRANCH=$(printf '%s' "$BRANCH" | tr '/_' '--' | tr -cd '[:alnum:].-'); IMAGE_TAG="branch-$SAFE_BRANCH"; fi
fi
BASE="https://raw.githubusercontent.com/RogueAssassin/RogueForge/$REF"
IMAGE_REF="ghcr.io/rogueassassin/rogueforge:$IMAGE_TAG"

env_value(){ awk -F= -v k="$1" '$1==k{print substr($0,index($0,"=")+1)}' .env | tail -n1 | tr -d '\r' || true; }
set_env(){ local key=$1 value=$2; if grep -q "^${key}=" .env; then sed -i "s#^${key}=.*#${key}=${value}#" .env; else printf '%s=%s\n' "$key" "$value" >> .env; fi; }

# Backups stay outside the install directory so RogueForge never discovers them as stacks.
STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_ROOT=${ROGUEFORGE_BACKUP_TMP:-${TMPDIR:-/tmp}/rogueforge/update-backups}; mkdir -p "$BACKUP_ROOT"
LEGACY_BACKUPS="$INSTALL_DIR/data/update-backups"
if [[ -d "$LEGACY_BACKUPS" ]]; then
  LEGACY_TARGET="$BACKUP_ROOT/legacy-$STAMP"; mkdir -p "$LEGACY_TARGET"
  shopt -s nullglob dotglob; legacy_items=("$LEGACY_BACKUPS"/*); ((${#legacy_items[@]})) && mv "${legacy_items[@]}" "$LEGACY_TARGET/"; shopt -u nullglob dotglob
  rmdir "$LEGACY_BACKUPS" 2>/dev/null || true
fi
BACKUP="$BACKUP_ROOT/$STAMP"; mkdir -p "$BACKUP"; cp -a compose.yaml .env "$BACKUP/"
[[ -f update.sh ]] && cp -a update.sh "$BACKUP/"; [[ -f update-testing.sh ]] && cp -a update-testing.sh "$BACKUP/"
# Keep the ten most recent update backups.
(cd "$BACKUP_ROOT" && ls -1dt ./[0-9]*-[0-9]*/ 2>/dev/null | tail -n +11 | xargs -r rm -rf) || true

deploy_engine=$(env_value ROGUEFORGE_DEPLOY_ENGINE | tr -d ' ')
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

# --- 1. Resolve and validate everything before anything is changed -----------
curl -fsSL "$BASE/compose.yaml" -o "$BACKUP/compose.download" || { echo "RogueForge source ref '$REF' is unavailable." >&2; exit 3; }
curl -fsSL "$BASE/update.sh" -o "$BACKUP/update.download" || { echo "RogueForge updater is unavailable on '$REF'." >&2; exit 3; }

MEDIA_ROOT=$(env_value ROGUEFORGE_MEDIA_ROOT); [[ -n $MEDIA_ROOT ]] || MEDIA_ROOT=/opt/media-server
COMPOSE_ROOT=$(env_value ROGUEFORGE_COMPOSE_ROOT)
LEGACY_STACKS=$(env_value ROGUEFORGE_STACKS_DIR)
if [[ -z $COMPOSE_ROOT ]]; then
  if [[ -n ${LEGACY_STACKS:-} ]]; then COMPOSE_ROOT=$LEGACY_STACKS
  else COMPOSE_ROOT=$MEDIA_ROOT; fi
fi
ENV_ROOT=$(env_value ROGUEFORGE_ENV_ROOT); [[ -n $ENV_ROOT ]] || ENV_ROOT=$COMPOSE_ROOT

echo "Media root:   $MEDIA_ROOT"
echo "Compose root: $COMPOSE_ROOT"
echo "Env root:     $ENV_ROOT"
[[ -d "$MEDIA_ROOT" ]] || { echo "Media root does not exist: $MEDIA_ROOT" >&2; exit 3; }
[[ -d "$COMPOSE_ROOT" ]] || { echo "Compose root does not exist: $COMPOSE_ROOT" >&2; exit 3; }
[[ -d "$ENV_ROOT" ]] || { echo "Env root does not exist: $ENV_ROOT" >&2; exit 3; }

# The health check must use the port and address this installation actually publishes.
HOST_PORT=$(env_value ROGUEFORGE_HOST_PORT | tr -d ' '); [[ $HOST_PORT =~ ^[0-9]+$ ]] || HOST_PORT=17810
HOST_BIND=$(env_value ROGUEFORGE_HOST_BIND | tr -d ' '); [[ -z $HOST_BIND || $HOST_BIND == 0.0.0.0 ]] && HOST_BIND=127.0.0.1
HEALTH_URL="http://$HOST_BIND:$HOST_PORT/health"
HEALTH_FILE="${TMPDIR:-/tmp}/rogueforge-health.$$"; trap 'rm -f "$HEALTH_FILE"' EXIT
wait_for_health(){
  local attempt
  for attempt in {1..30}; do
    if curl -fsS --max-time 5 "$HEALTH_URL" >"$HEALTH_FILE" 2>/dev/null; then return 0; fi
    sleep 2
  done
  return 1
}

# --- 2. Pull FIRST so a missing tag cannot leave the configuration half-updated ---
RUNNING_IMAGE=$("$deploy_engine" inspect rogueforge --format '{{.Image}}' 2>/dev/null || true)
"$deploy_engine" pull "$IMAGE_REF" || { echo "RogueForge image tag '$IMAGE_TAG' is not published in GHCR. Nothing was changed." >&2; exit 4; }
EXPECTED_IMAGE=$("$deploy_engine" image inspect "$IMAGE_REF" --format '{{.Id}}' 2>/dev/null || true)

# Keep the image that is running now addressable so a failed update can return to it.
ROLLBACK_REF=""
if [[ -n $RUNNING_IMAGE && $RUNNING_IMAGE != "$EXPECTED_IMAGE" ]]; then
  ROLLBACK_REF="localhost/rogueforge-rollback:$STAMP"
  "$deploy_engine" tag "$RUNNING_IMAGE" "$ROLLBACK_REF" 2>/dev/null || ROLLBACK_REF=""
fi

echo "Running image: ${RUNNING_IMAGE:-none}"
echo "Pulled image:  ${EXPECTED_IMAGE:-unknown}"

# --- 3. Install the updated deployment files ---------------------------------
install -m 0644 "$BACKUP/compose.download" "$INSTALL_DIR/compose.yaml"
# Do not replace the running updater in-place. Bash may still be reading this file;
# self-overwriting it can splice old/new script contents and cause impossible syntax errors.

set_env ROGUEFORGE_IMAGE "$IMAGE_REF"
set_env ROGUEFORGE_CHANNEL "$CHANNEL"
set_env ROGUEFORGE_INSTALL_DIR "$INSTALL_DIR"
set_env ROGUEFORGE_DATA_DIR "$INSTALL_DIR/data"
set_env ROGUEFORGE_AUTH_FILE "/opt/rogueforge/data/auth.json"
set_env ROGUEFORGE_OPERATIONS_FILE "/opt/rogueforge/data/operations.json"
set_env ROGUEFORGE_MEDIA_ROOT "$MEDIA_ROOT"
set_env ROGUEFORGE_COMPOSE_ROOT "$COMPOSE_ROOT"
set_env ROGUEFORGE_ENV_ROOT "$ENV_ROOT"
set_env ROGUEFORGE_STACKS_DIR "$COMPOSE_ROOT"

# Environment revisions are intentionally append-only and only exist when a
# release introduces new runtime settings. The administrator's existing .env is
# otherwise left untouched.

rollback(){
  local reason=$1
  echo "Update failed: $reason" >&2
  if [[ -z $RUNNING_IMAGE ]]; then
    echo "RogueForge was not running before the update, so automatic rollback is not possible. Deployment backup remains at $BACKUP" >&2
    return 1
  fi
  echo "Rolling back to the previous deployment files and image..." >&2
  cp -a "$BACKUP/compose.yaml" "$BACKUP/.env" "$INSTALL_DIR/"
  # When the image itself changed, the restored tag may now resolve to the new image.
  [[ -n $ROLLBACK_REF ]] && set_env ROGUEFORGE_IMAGE "$ROLLBACK_REF"
  "$deploy_engine" rm -f rogueforge >/dev/null 2>&1 || true
  if "${compose_cmd[@]}" up -d --remove-orphans && wait_for_health; then
    echo "Rollback succeeded. Deployment backup remains at $BACKUP" >&2
    if [[ -n $ROLLBACK_REF ]]; then
      echo "ROGUEFORGE_IMAGE in .env now points at $ROLLBACK_REF (the version you were running)." >&2
      echo "Set ROGUEFORGE_IMAGE back to a published tag when you are ready to try again." >&2
    fi
  else
    echo "Rollback did not restore a healthy service. Deployment backup remains at $BACKUP" >&2
    "${compose_cmd[@]}" ps >&2 || true; "$deploy_engine" logs --tail 100 rogueforge >&2 || true
  fi
  return 1
}

# --- 4. Recreate and verify --------------------------------------------------
if [[ -n "$EXPECTED_IMAGE" && -n "$RUNNING_IMAGE" && "$EXPECTED_IMAGE" != "$RUNNING_IMAGE" ]]; then
  echo "RogueForge image changed; replacing existing container..."
  "$deploy_engine" rm -f rogueforge >/dev/null
fi

if ! "${compose_cmd[@]}" up -d --remove-orphans; then
  rollback "Compose recreate failed." || true
  exit 5
fi

NEW_IMAGE=$("$deploy_engine" inspect rogueforge --format '{{.Image}}' 2>/dev/null || true)
if [[ -n "$EXPECTED_IMAGE" && "$NEW_IMAGE" != "$EXPECTED_IMAGE" ]]; then
  echo "RogueForge update verification failed." >&2
  echo "Expected image: $EXPECTED_IMAGE" >&2
  echo "Running image:  ${NEW_IMAGE:-missing}" >&2
  rollback "The running image is not the one that was pulled." || true
  exit 6
fi

echo "Verified running image: ${NEW_IMAGE:-unknown}"

if wait_for_health; then
  echo; cat "$HEALTH_FILE"; echo
  echo "RogueForge $CHANNEL update complete."
  echo "Media root:   $MEDIA_ROOT"
  echo "Compose root: $COMPOSE_ROOT"
  echo "Env root:     $ENV_ROOT"
  [[ $CHANNEL == testing ]] && echo "TESTING BUILD ACTIVE: $REF ($IMAGE_TAG)"
  # The rollback tag is only needed while the update can still fail.
  [[ -n $ROLLBACK_REF ]] && "$deploy_engine" rmi "$ROLLBACK_REF" >/dev/null 2>&1 || true
  install -m 0755 "$BACKUP/update.download" "$INSTALL_DIR/update.sh"
  echo "Updater refreshed for the next run."
  exit 0
fi

rollback "Health check failed." || true
"${compose_cmd[@]}" ps >&2 || true; "$deploy_engine" logs --tail 100 rogueforge >&2 || true
exit 1
