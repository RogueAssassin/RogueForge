#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE=${ROGUEFORGE_IMAGE:-ghcr.io/rogueassassin/rogueforge:0.4.2}
TARGET=${ROGUEFORGE_TARGET:-/opt/media-server/rogueforge}
BACKUP_ROOT=${ROGUEFORGE_BACKUP_ROOT:-/opt/rogueforge-backups}
SOURCE=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ASSUME_YES=false

[[ ${1:-} == --yes ]] && ASSUME_YES=true

if [[ $EUID -eq 0 ]]; then
  echo "Run this script as the rootless Podman owner (administrator), not with sudo." >&2
  exit 1
fi
if [[ $TARGET != /* || $BACKUP_ROOT != /* || $TARGET =~ [[:space:]] || $BACKUP_ROOT =~ [[:space:]] ]]; then
  echo "Target and backup paths must be absolute and contain no whitespace." >&2
  exit 2
fi
if [[ $SOURCE == "$TARGET" ]]; then
  echo "Extract the new release outside $TARGET before running this migration." >&2
  exit 2
fi
for command in podman podman-compose sudo python3 curl awk; do
  command -v "$command" >/dev/null || { echo "Missing required command: $command" >&2; exit 2; }
done

echo "RogueForge 0.4.2 migration"
echo "  Image:  $IMAGE"
echo "  Target: $TARGET"
echo
echo "Preflight: pulling the GHCR image before changing the current installation..."
podman pull "$IMAGE"
podman network exists media-net || { echo "The rootless media-net network does not exist." >&2; exit 2; }

if [[ $ASSUME_YES != true ]]; then
  read -r -p "The image is available. Back up and replace the old RogueForge installation? [y/N] " answer
  [[ $answer == y || $answer == Y ]] || { echo "Migration cancelled; nothing was changed."; exit 0; }
fi

timestamp=$(date +%Y%m%d%H%M%S)
backup="$BACKUP_ROOT/rogueforge-$timestamp"
old_systemd=false
migration_complete=false

rollback() {
  status=$?
  if [[ $migration_complete != true ]]; then
    echo "Migration failed; attempting rollback from $backup" >&2
    podman rm -f rogueforge >/dev/null 2>&1 || true
    if [[ -d $backup ]]; then
      sudo mv "$TARGET" "$TARGET.failed-$timestamp" 2>/dev/null || true
      sudo mv "$backup" "$TARGET" 2>/dev/null || true
      sudo chown -R "$(id -u):$(id -g)" "$TARGET" 2>/dev/null || true
      if [[ -f $TARGET/compose.yaml ]]; then
        (cd "$TARGET" && podman-compose up -d) || true
      fi
    fi
    [[ $old_systemd == true ]] && sudo systemctl enable --now rogueforge || true
  fi
  exit "$status"
}
trap rollback ERR

if sudo systemctl is-active --quiet rogueforge 2>/dev/null; then
  old_systemd=true
fi
sudo systemctl disable --now rogueforge 2>/dev/null || true
podman rm -f rogueforge >/dev/null 2>&1 || true

sudo install -d -m 0755 "$BACKUP_ROOT"
if [[ -d $TARGET ]]; then
  sudo mv "$TARGET" "$backup"
fi
sudo install -d -m 0755 "$TARGET"

for file in Containerfile compose.yaml compose.build.yaml setup-auth.py rogueforge.py README.md SECURITY.md CHANGELOG.md MILESTONES.md .env.example .containerignore .gitattributes; do
  [[ -e $SOURCE/$file ]] && sudo cp -a "$SOURCE/$file" "$TARGET/"
done
for directory in static docs systemd scripts; do
  [[ -d $SOURCE/$directory ]] && sudo cp -a "$SOURCE/$directory" "$TARGET/"
done

if [[ -f $backup/.env ]]; then
  sudo cp -a "$backup/.env" "$TARGET/.env"
else
  sudo cp "$TARGET/.env.example" "$TARGET/.env"
fi
if [[ -d $backup/data ]]; then
  sudo cp -a "$backup/data" "$TARGET/data"
else
  sudo install -d -m 0700 "$TARGET/data"
fi
sudo chown -R "$(id -u):$(id -g)" "$TARGET"

cd "$TARGET"
if [[ ! -f data/auth.json ]]; then
  echo "A RogueForge administrator must be provisioned."
  python3 setup-auth.py --username administrator
fi
chmod 700 data
chmod 600 data/auth.json

podman-compose pull
podman-compose up -d
host_port=$(awk -F= '$1 == "ROGUEFORGE_HOST_PORT" {print $2}' .env | tail -n 1)
host_port=${host_port:-17810}
curl --fail --silent --show-error --retry 12 --retry-delay 2 "http://127.0.0.1:$host_port/health" >/dev/null
podman exec nginx-proxy-manager getent hosts rogueforge

migration_complete=true
trap - ERR
echo
echo "RogueForge 0.4.2 migration completed."
echo "  Backup: $backup"
echo "  LAN:    http://$(hostname -I | awk '{print $1}'):$host_port"
echo "  NPM:    http://rogueforge:7810"
