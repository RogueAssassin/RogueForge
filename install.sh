#!/usr/bin/env bash
set -Eeuo pipefail
if [[ $EUID -ne 0 ]]; then echo "Run with sudo"; exit 1; fi
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install -d -m 0755 /opt/rogueforge /opt/rogueforge/static
install -m 0755 "$SRC/rogueforge.py" /opt/rogueforge/rogueforge.py
install -m 0644 "$SRC/static/index.html" "$SRC/static/styles.css" "$SRC/static/app.js" /opt/rogueforge/static/
install -m 0644 "$SRC/systemd/rogueforge.service" /etc/systemd/system/rogueforge.service
[[ -f /etc/default/rogueforge ]] || install -m 0644 "$SRC/rogueforge.default" /etc/default/rogueforge
systemctl daemon-reload
systemctl enable --now rogueforge.service
echo "RogueForge installed. Status:"
systemctl status rogueforge.service --no-pager -l || true
echo "Local URL: http://127.0.0.1:7810"
