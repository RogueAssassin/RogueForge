# RogueForge installation and proxy guide

## Directory layout

Keep RogueForge separate from the Compose projects it manages:

```text
/opt/rogueforge/           RogueForge application
/opt/media-server/         Your existing Compose projects
/etc/default/rogueforge    Runtime configuration
```

The stacks directory may be any absolute path without whitespace.

## Stop an existing installation

```bash
sudo systemctl stop rogueforge
```

The service remains installed and can be restarted with:

```bash
sudo systemctl start rogueforge
```

## Determine whether Podman is rootless

Run these commands without `sudo`, using the account that normally manages the containers:

```bash
whoami
id -u
podman ps -a
podman info --format '{{.Host.Security.Rootless}}'
```

If the final command returns `true`, use the `--podman-user` installer option. The official Podman socket locations are:

```text
Rootful:  /run/podman/podman.sock
Rootless: /run/user/<UID>/podman/podman.sock
```

## Install for rootless Podman

Replace `rogue` and the stacks path with the correct values:

```bash
sudo ./install.sh \
  --podman-user rogue \
  --stacks-dir /opt/media-server
```

This performs four related operations:

1. Enables lingering for the selected user.
2. Enables and starts that user's `podman.socket` unit.
3. Configures RogueForge to use `/run/user/<UID>/podman/podman.sock`.
4. Runs `podman-compose` as the selected user for stack actions.

Verify the generated configuration:

```bash
sudo grep '^ROGUEFORGE_' /etc/default/rogueforge
sudo systemctl restart rogueforge
curl http://127.0.0.1:7810/api/status
curl http://127.0.0.1:7810/api/containers
```

## Install for rootful Podman

Use rootful mode only when `sudo podman ps -a` shows the expected containers:

```bash
sudo ./install.sh \
  --engine podman \
  --socket /run/podman/podman.sock \
  --stacks-dir /opt/media-server
```

## Configure Nginx Proxy Manager

### Install RogueForge for a proxy on the same network

If Nginx Proxy Manager runs inside a container, it normally cannot reach the host's `127.0.0.1`. Bind RogueForge to the host network interfaces and restrict port 7810 with the server firewall:

```bash
sudo ./install.sh \
  --podman-user rogue \
  --stacks-dir /opt/media-server \
  --bind 0.0.0.0 \
  --proxy-hostname manage.roguegaming.com.au
```

Use the server's private LAN address as the upstream. Do not forward port 7810 directly from the internet.

### Add the Proxy Host

In Nginx Proxy Manager choose **Hosts → Proxy Hosts → Add Proxy Host** and set:

```text
Domain Names:       manage.roguegaming.com.au
Scheme:             http
Forward Hostname:   <RogueForge server LAN IP>
Forward Port:       7810
Cache Assets:       Off
Block Common Exploits: On
Websockets Support: On
```

In the **SSL** section:

```text
SSL Certificate:    Request a new Let's Encrypt certificate
Force SSL:          On
HTTP/2 Support:     On
HSTS:               On after confirming HTTPS works
```

### Protect the management interface

RogueForge 0.4.0 protects privileged operations with its administrator account. An Nginx Proxy Manager **Access List** can still be attached as defence in depth, and a VPN or identity-aware proxy remains preferable for a management surface.

Do not expose the Podman socket itself over TCP. RogueForge accesses it locally through Unix socket permissions.

### DNS

Create a DNS record for `manage.roguegaming.com.au` pointing to the public address that reaches Nginx Proxy Manager. Only ports 80 and 443 should be forwarded to Nginx Proxy Manager; port 7810 should remain private.

## Troubleshooting

### Connected, but zero containers

Compare both stores:

```bash
podman ps -a
sudo podman ps -a
```

Whichever command displays your workloads identifies the correct context. For the first command, reinstall using `--podman-user <username>`. For the second, use the rootful socket.

### Check the rootless socket

```bash
uid=$(id -u)
systemctl --user enable --now podman.socket
ls -l "/run/user/$uid/podman/podman.sock"
curl --unix-socket "/run/user/$uid/podman/podman.sock" http://localhost/version
```

### Review RogueForge logs

```bash
sudo journalctl -u rogueforge -n 100 --no-pager
sudo journalctl -u rogueforge -f
```

### Confirm the upstream is reachable from the proxy server

```bash
curl http://<RogueForge-server-LAN-IP>:7810/health
```

If this fails, check the RogueForge bind address, host firewall, and routing between Nginx Proxy Manager and the RogueForge host.
