#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR=/opt/rogueforge
STACKS_DIR=/opt/stacks
CONFIG_FILE=/etc/default/rogueforge
SERVICE_FILE=/etc/systemd/system/rogueforge.service
BIND=127.0.0.1
PORT=7810
ENGINE=auto
SOCKET=
PODMAN_USER=
PROXY_HOSTNAME=
INTERACTIVE=false

usage() {
  cat <<'EOF'
RogueForge installer

Usage:
  sudo ./install.sh [options]

Options:
  --interactive             Prompt for installation settings.
  --install-dir PATH        Application directory (default: /opt/rogueforge).
  --stacks-dir PATH         Compose stacks directory (default: /opt/stacks).
  --bind ADDRESS            Listen address (default: 127.0.0.1).
  --port PORT               Listen port (default: 7810).
  --engine auto|docker|podman
                            Container engine (default: auto).
  --socket PATH             Explicit Docker or Podman socket.
  --podman-user USER        Manage rootless containers owned by USER.
  --proxy-hostname NAME     Record the public reverse-proxy hostname.
  --config-file PATH        Environment file (default: /etc/default/rogueforge).
  -h, --help                Show this help.

Examples:
  sudo ./install.sh
  sudo ./install.sh --interactive
  sudo ./install.sh --stacks-dir /srv/compose
  sudo ./install.sh --install-dir /srv/rogueforge --stacks-dir /mnt/apps/stacks
  sudo ./install.sh --podman-user rogue --stacks-dir /opt/media-server
EOF
}

while (($#)); do
  case "$1" in
    --interactive) INTERACTIVE=true; shift ;;
    --install-dir) INSTALL_DIR=${2:?Missing path after --install-dir}; shift 2 ;;
    --stacks-dir) STACKS_DIR=${2:?Missing path after --stacks-dir}; shift 2 ;;
    --bind) BIND=${2:?Missing address after --bind}; shift 2 ;;
    --port) PORT=${2:?Missing port after --port}; shift 2 ;;
    --engine) ENGINE=${2:?Missing engine after --engine}; shift 2 ;;
    --socket) SOCKET=${2:?Missing path after --socket}; shift 2 ;;
    --podman-user) PODMAN_USER=${2:?Missing user after --podman-user}; shift 2 ;;
    --proxy-hostname) PROXY_HOSTNAME=${2:?Missing name after --proxy-hostname}; shift 2 ;;
    --config-file) CONFIG_FILE=${2:?Missing path after --config-file}; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi

prompt() {
  local label=$1 current=$2 answer
  read -r -p "$label [$current]: " answer
  printf '%s' "${answer:-$current}"
}

if [[ $INTERACTIVE == true ]]; then
  echo "RogueForge guided installation"
  echo "The application and managed stacks should use separate directories."
  INSTALL_DIR=$(prompt "Application directory" "$INSTALL_DIR")
  STACKS_DIR=$(prompt "Compose stacks directory" "$STACKS_DIR")
  BIND=$(prompt "Listen address" "$BIND")
  PORT=$(prompt "Listen port" "$PORT")
  ENGINE=$(prompt "Engine (auto/docker/podman)" "$ENGINE")
  if [[ $ENGINE == podman ]]; then
    PODMAN_USER=$(prompt "Rootless Podman user (leave blank for rootful)" "$PODMAN_USER")
  fi
fi

for path in "$INSTALL_DIR" "$STACKS_DIR" "$CONFIG_FILE"; do
  if [[ $path != /* || $path =~ [[:space:]] ]]; then
    echo "Paths must be absolute and contain no whitespace: $path" >&2
    exit 2
  fi
done
if [[ $INSTALL_DIR == "$STACKS_DIR" ]]; then
  echo "The application and stacks directories must be different." >&2
  exit 2
fi
if [[ ! $PORT =~ ^[0-9]+$ ]] || ((PORT < 1 || PORT > 65535)); then
  echo "Port must be between 1 and 65535." >&2
  exit 2
fi
if [[ $ENGINE != auto && $ENGINE != docker && $ENGINE != podman ]]; then
  echo "Engine must be auto, docker, or podman." >&2
  exit 2
fi
if [[ -n $PODMAN_USER ]]; then
  if ! id "$PODMAN_USER" >/dev/null 2>&1; then
    echo "Podman user does not exist: $PODMAN_USER" >&2
    exit 2
  fi
  ENGINE=podman
  podman_uid=$(id -u "$PODMAN_USER")
  SOCKET="/run/user/$podman_uid/podman/podman.sock"
  loginctl enable-linger "$PODMAN_USER"
  runuser -u "$PODMAN_USER" -- env XDG_RUNTIME_DIR="/run/user/$podman_uid" systemctl --user enable --now podman.socket
fi

SRC=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
install -d -m 0755 "$INSTALL_DIR" "$INSTALL_DIR/static" "$INSTALL_DIR/data" "$STACKS_DIR" "$(dirname "$CONFIG_FILE")"
install -m 0755 "$SRC/rogueforge.py" "$INSTALL_DIR/rogueforge.py"
install -m 0755 "$SRC/setup-auth.py" "$INSTALL_DIR/setup-auth.py"
install -m 0644 "$SRC/static/index.html" "$SRC/static/styles.css" "$SRC/static/app.js" "$INSTALL_DIR/static/"

if [[ -f $CONFIG_FILE ]]; then
  cp -a "$CONFIG_FILE" "$CONFIG_FILE.backup-$(date +%Y%m%d%H%M%S)"
fi
{
  printf 'ROGUEFORGE_BIND=%q\n' "$BIND"
  printf 'ROGUEFORGE_PORT=%q\n' "$PORT"
  printf 'ROGUEFORGE_STACKS_DIR=%q\n' "$STACKS_DIR"
  printf 'ROGUEFORGE_ENGINE=%q\n' "$ENGINE"
  printf 'ROGUEFORGE_AUTH_FILE=%q\n' "$INSTALL_DIR/data/auth.json"
  [[ -n $SOCKET ]] && printf 'ROGUEFORGE_SOCKET=%q\n' "$SOCKET"
  [[ -n $PODMAN_USER ]] && printf 'ROGUEFORGE_PODMAN_USER=%q\n' "$PODMAN_USER"
  [[ -n $PROXY_HOSTNAME ]] && printf 'ROGUEFORGE_PUBLIC_URL=https://%q\n' "$PROXY_HOSTNAME"
  printf 'ROGUEFORGE_PODMAN_COMPOSE=/usr/bin/podman-compose\n'
  printf 'ROGUEFORGE_PODMAN=/usr/bin/podman\n'
  printf 'ROGUEFORGE_DOCKER=/usr/bin/docker\n'
} > "$CONFIG_FILE"
chmod 0644 "$CONFIG_FILE"

escape_sed() { printf '%s' "$1" | sed 's/[&|]/\\&/g'; }
install_escaped=$(escape_sed "$INSTALL_DIR")
stacks_escaped=$(escape_sed "$STACKS_DIR")
config_escaped=$(escape_sed "$CONFIG_FILE")
protect_home=true
[[ -n $PODMAN_USER ]] && protect_home=false
sed -e "s|@INSTALL_DIR@|$install_escaped|g" \
    -e "s|@STACKS_DIR@|$stacks_escaped|g" \
    -e "s|@CONFIG_FILE@|$config_escaped|g" \
    -e "s|@PROTECT_HOME@|$protect_home|g" \
    "$SRC/systemd/rogueforge.service" > "$SERVICE_FILE"
chmod 0644 "$SERVICE_FILE"

systemctl daemon-reload
systemctl enable --now rogueforge.service

echo
echo "RogueForge installed successfully."
echo "  Application: $INSTALL_DIR"
echo "  Stacks:      $STACKS_DIR"
echo "  Config:      $CONFIG_FILE"
echo "  Local URL:   http://$BIND:$PORT"
[[ -n $PODMAN_USER ]] && echo "  Podman user: $PODMAN_USER ($SOCKET)"
[[ -n $PROXY_HOSTNAME ]] && echo "  Proxy URL:   https://$PROXY_HOSTNAME"
if [[ ! -f $INSTALL_DIR/data/auth.json ]]; then
  echo "  Account:     NOT CONFIGURED"
  echo "  Run: sudo python3 $INSTALL_DIR/setup-auth.py --username administrator --auth-file $INSTALL_DIR/data/auth.json"
fi
echo
systemctl status rogueforge.service --no-pager -l || true
