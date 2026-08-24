#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR=${ROGUEFORGE_INSTALL_DIR:-/opt/media-server/rogueforge}
STACKS_DIR=${ROGUEFORGE_STACKS_DIR:-/opt/media-server}
ICONS_DIR=${ROGUEFORGE_ICONS_DIR:-/opt/media-server/rogue-dashboard/app/static/icons}
IMAGE=${ROGUEFORGE_IMAGE:-ghcr.io/rogueassassin/rogueforge:0.4.2}
HOST_PORT=${ROGUEFORGE_HOST_PORT:-17810}
PUBLIC_URL=${ROGUEFORGE_PUBLIC_URL:-https://manage.roguegaming.com.au}
NETWORK=${ROGUEFORGE_NETWORK:-media-net}
USERNAME=${ROGUEFORGE_ADMIN_USERNAME:-administrator}
ASSUME_YES=false

usage() {
  cat <<'EOF'
RogueForge 0.4.2 first-install helper for rootless Podman

Usage: ./install.sh [options]

  --install-dir PATH   Deployment folder (default: /opt/media-server/rogueforge)
  --stacks-dir PATH    Compose stacks root (default: /opt/media-server)
  --icons-dir PATH     Existing local icon folder
  --image IMAGE        GHCR image (default: ghcr.io/rogueassassin/rogueforge:0.4.2)
  --host-port PORT     LAN port (default: 17810; container port remains 7810)
  --public-url URL     Public reverse-proxy URL
  --network NAME       Shared Podman network (default: media-net)
  --username NAME      Initial administrator (default: administrator)
  --yes                Skip confirmation
  -h, --help           Show this help

Run as the rootless Podman owner, not with sudo.
EOF
}

while (($#)); do
  case "$1" in
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

if [[ $EUID -eq 0 ]]; then
  echo "Run as the rootless Podman owner, not with sudo." >&2
  exit 1
fi
for command in podman podman-compose python3 curl sudo awk systemctl; do
  command -v "$command" >/dev/null || { echo "Missing required command: $command" >&2; exit 2; }
done
for path in "$INSTALL_DIR" "$STACKS_DIR" "$ICONS_DIR"; do
  [[ $path == /* && ! $path =~ [[:space:]] ]] || { echo "Paths must be absolute and contain no whitespace: $path" >&2; exit 2; }
done
[[ $INSTALL_DIR != "$STACKS_DIR" ]] || { echo "Install and stacks directories must differ." >&2; exit 2; }
[[ $HOST_PORT =~ ^[0-9]+$ ]] && ((HOST_PORT >= 1 && HOST_PORT <= 65535)) || { echo "Invalid host port: $HOST_PORT" >&2; exit 2; }
[[ $NETWORK =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "Invalid network name: $NETWORK" >&2; exit 2; }

SOURCE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if [[ ! -f $SOURCE/compose.yaml || ! -f $SOURCE/setup-auth.py ]]; then
  echo "Run this script from a complete RogueForge release or Git clone." >&2
  exit 2
fi

echo "Preflight: pulling $IMAGE before changing the host..."
podman pull "$IMAGE"
podman info >/dev/null
systemctl --user enable --now podman.socket
socket="/run/user/$(id -u)/podman/podman.sock"
[[ -S $socket ]] || { echo "Rootless Podman socket was not created: $socket" >&2; exit 2; }

if [[ -e $INSTALL_DIR/compose.yaml || -e $INSTALL_DIR/data/auth.json ]]; then
  echo "An existing RogueForge installation was found at $INSTALL_DIR." >&2
  echo "Use the upgrade/migration procedure instead of the first-install helper." >&2
  exit 3
fi

cat <<EOF
RogueForge 0.4.2 will be installed with:
  Folder:       $INSTALL_DIR
  Stacks:       $STACKS_DIR
  Icons:        $ICONS_DIR
  Image:        $IMAGE
  LAN:          http://<server-ip>:$HOST_PORT
  NPM upstream: http://rogueforge:7810
  Network:      $NETWORK
EOF
if [[ $ASSUME_YES != true ]]; then
  read -r -p "Continue? [y/N] " answer
  [[ $answer == y || $answer == Y ]] || { echo "Installation cancelled; nothing changed."; exit 0; }
fi

sudo install -d -m 0755 "$INSTALL_DIR" "$STACKS_DIR"
sudo install -d -m 0700 "$INSTALL_DIR/data"
for file in compose.yaml setup-auth.py .env.example; do
  sudo install -m 0644 "$SOURCE/$file" "$INSTALL_DIR/$file"
done
sudo install -m 0755 "$SOURCE/upgrade.sh" "$INSTALL_DIR/upgrade.sh"
sudo chown -R "$(id -u):$(id -g)" "$INSTALL_DIR"

cat > "$INSTALL_DIR/.env" <<EOF
PODMAN_UID=$(id -u)
ROGUEFORGE_HOST_PORT=$HOST_PORT
ROGUEFORGE_IMAGE=$IMAGE
ROGUEFORGE_STACKS_DIR=$STACKS_DIR
ROGUEFORGE_ICONS_DIR=$ICONS_DIR
ROGUEFORGE_PUBLIC_URL=$PUBLIC_URL
ROGUEFORGE_NETWORK=$NETWORK
EOF
chmod 600 "$INSTALL_DIR/.env"

cd "$INSTALL_DIR"
python3 setup-auth.py --username "$USERNAME"
chmod 700 data
chmod 600 data/auth.json

podman network exists "$NETWORK" || podman network create "$NETWORK"
podman-compose pull
podman-compose up -d
curl --fail --silent --show-error --retry 15 --retry-delay 2 --retry-all-errors "http://127.0.0.1:$HOST_PORT/health" >/dev/null

echo
echo "RogueForge 0.4.2 is installed and healthy."
echo "  Deployment: $INSTALL_DIR"
echo "  LAN:        http://$(hostname -I | awk '{print $1}'):$HOST_PORT"
echo "  NPM:        http://rogueforge:7810"
echo "  Account:    $USERNAME"
