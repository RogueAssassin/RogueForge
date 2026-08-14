#!/usr/bin/env python3
from __future__ import annotations

from http import HTTPStatus
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlparse

VERSION = "0.1.0"
PORT = int(os.environ.get("ROGUEFORGE_PORT", "7810"))
BIND = os.environ.get("ROGUEFORGE_BIND", "127.0.0.1")
STACKS_DIR = Path(os.environ.get("ROGUEFORGE_STACKS_DIR", "/opt/media-server")).resolve()
STATIC_DIR = Path(os.environ.get("ROGUEFORGE_STATIC_DIR", Path(__file__).with_name("static"))).resolve()
ENGINE = os.environ.get("ROGUEFORGE_ENGINE", "auto").strip().lower()
SOCKET_PATH = os.environ.get("ROGUEFORGE_SOCKET", "").strip()
MAX_BODY = 2_000_000
STACK_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
COMPOSE_NAMES = ("podman-compose.yaml", "compose.podman.yaml", "docker-compose.yaml", "docker-compose.yml", "compose.yaml", "compose.yml")


class UnixHTTPConnection(HTTPConnection):
    def __init__(self, path: str):
        super().__init__("localhost", timeout=5)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.path)


def request_engine(method: str, path: str, body: bytes | None = None, maximum: int = 5_000_000):
    conn = UnixHTTPConnection(runtime()["socket"])
    try:
        conn.request(method, path, body=body, headers={"Accept": "application/json"})
        res = conn.getresponse()
        raw = res.read(maximum)
        if res.status >= 400:
            raise RuntimeError(f"engine HTTP {res.status}: {raw[:500].decode(errors='replace')}")
        if not raw:
            return None
        ctype = res.getheader("content-type", "")
        if "json" in ctype or raw[:1] in (b"{", b"["):
            return json.loads(raw)
        return raw.decode(errors="replace")
    finally:
        conn.close()


_runtime = None
def runtime():
    global _runtime
    if _runtime:
        return _runtime
    candidates = []
    if SOCKET_PATH:
        candidates.append(SOCKET_PATH)
    candidates += ["/run/podman/podman.sock", "/var/run/docker.sock"]
    for p in candidates:
        if not p or not Path(p).exists():
            continue
        try:
            conn = UnixHTTPConnection(p)
            conn.request("GET", "/version")
            res = conn.getresponse()
            raw = res.read(200_000)
            conn.close()
            if res.status >= 400:
                continue
            data = json.loads(raw or b"{}")
            blob = json.dumps(data).lower()
            kind = "podman" if ("podman" in blob or "libpod" in blob) else "docker"
            if ENGINE not in ("auto", kind):
                continue
            _runtime = {
                "engine": kind,
                "socket": p,
                "version": str(data.get("Version") or data.get("version") or "unknown"),
                "apiVersion": str(data.get("ApiVersion") or data.get("APIVersion") or "unknown"),
            }
            return _runtime
        except Exception:
            continue
    raise RuntimeError("No matching Docker/Podman API socket detected")


def compose_file(stack_dir: Path) -> Path | None:
    for name in COMPOSE_NAMES:
        p = stack_dir / name
        if p.is_file():
            return p
    return None


def safe_stack(name: str) -> Path:
    if not STACK_NAME.fullmatch(name):
        raise ValueError("invalid stack name")
    p = (STACKS_DIR / name).resolve()
    if p.parent != STACKS_DIR:
        raise ValueError("stack path escapes stacks directory")
    if not p.is_dir():
        raise FileNotFoundError(name)
    return p


def discover_stacks():
    result = []
    if not STACKS_DIR.is_dir():
        return result
    for p in sorted(STACKS_DIR.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        cf = compose_file(p)
        if not cf:
            continue
        result.append({
            "name": p.name,
            "composeFile": cf.name,
            "hasEnv": (p / ".env").is_file(),
            "engineHint": "podman" if "podman" in cf.name else ("docker" if "docker" in cf.name else "portable"),
        })
    return result


def compose_command(stack: str, args: list[str]) -> list[str]:
    directory = safe_stack(stack)
    cf = compose_file(directory)
    if not cf:
        raise RuntimeError("compose file not found")
    rt = runtime()
    if rt["engine"] == "podman":
        binary = os.environ.get("ROGUEFORGE_PODMAN_COMPOSE", "/usr/bin/podman-compose")
        cmd = [binary]
        if (directory / ".env").is_file():
            cmd += ["--env-file", ".env"]
        cmd += ["-f", cf.name]
    else:
        docker = os.environ.get("ROGUEFORGE_DOCKER", "/usr/bin/docker")
        cmd = [docker, "compose"]
        if (directory / ".env").is_file():
            cmd += ["--env-file", ".env"]
        cmd += ["-f", cf.name]
    return cmd + args


def run_stack_action(stack: str, action: str):
    directory = safe_stack(stack)
    mapping = {
        "start": ["up", "-d"],
        "stop": ["down"],
        "restart": ["down"],
        "pull": ["pull"],
    }
    if action not in mapping:
        raise ValueError("unsupported action")
    env = os.environ.copy()
    if action == "restart":
        first = subprocess.run(compose_command(stack, ["down"]), cwd=directory, env=env, text=True, capture_output=True, timeout=600)
        if first.returncode:
            return {"ok": False, "output": first.stdout + first.stderr}
        proc = subprocess.run(compose_command(stack, ["up", "-d"]), cwd=directory, env=env, text=True, capture_output=True, timeout=900)
    else:
        proc = subprocess.run(compose_command(stack, mapping[action]), cwd=directory, env=env, text=True, capture_output=True, timeout=900)
    return {"ok": proc.returncode == 0, "output": (proc.stdout + proc.stderr)[-100_000:]}


def containers():
    raw = request_engine("GET", "/containers/json?all=1")
    result = []
    for item in raw or []:
        names = item.get("Names") or []
        result.append({
            "id": str(item.get("Id", ""))[:12],
            "name": (names[0].lstrip("/") if names else "unnamed"),
            "image": item.get("Image", "unknown"),
            "state": item.get("State", "unknown"),
            "status": item.get("Status", "unknown"),
            "labels": item.get("Labels") or {},
            "ports": item.get("Ports") or [],
        })
    return sorted(result, key=lambda x: (x["state"] != "running", x["name"].lower()))


def container_action(cid: str, action: str):
    if not re.fullmatch(r"[0-9a-fA-F]{12,64}", cid):
        raise ValueError("invalid container id")
    if action not in ("start", "stop", "restart"):
        raise ValueError("unsupported action")
    suffix = "?t=10" if action in ("stop", "restart") else ""
    request_engine("POST", f"/containers/{cid}/{action}{suffix}", b"")
    return {"ok": True}


def container_logs(cid: str):
    if not re.fullmatch(r"[0-9a-fA-F]{12,64}", cid):
        raise ValueError("invalid container id")
    # Docker-compatible logs can be multiplexed. For the MVP return printable payload.
    data = request_engine("GET", f"/containers/{cid}/logs?stdout=1&stderr=1&tail=250&timestamps=1", maximum=2_000_000)
    if isinstance(data, str):
        return data
    if isinstance(data, bytes):
        return data.decode(errors="replace")
    return json.dumps(data, indent=2)


class Handler(BaseHTTPRequestHandler):
    server_version = f"RogueForge/{VERSION}"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))

    def send_json(self, value, status=200):
        raw = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def read_json(self):
        length = min(int(self.headers.get("content-length", "0") or 0), MAX_BODY)
        raw = self.rfile.read(length)
        return json.loads(raw or b"{}")

    def send_static(self, rel):
        rel = "index.html" if rel in ("", "/") else rel.lstrip("/")
        p = (STATIC_DIR / rel).resolve()
        if STATIC_DIR not in p.parents and p != STATIC_DIR:
            self.send_error(404)
            return
        if not p.is_file():
            p = STATIC_DIR / "index.html"
        data = p.read_bytes()
        self.send_response(200)
        self.send_header("content-type", mimetypes.guess_type(str(p))[0] or "application/octet-stream")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        try:
            u = urlparse(self.path)
            if u.path == "/api/status":
                self.send_json({"version": VERSION, **runtime(), "stacksDir": str(STACKS_DIR)})
                return
            if u.path == "/api/stacks":
                self.send_json(discover_stacks())
                return
            if u.path == "/api/containers":
                self.send_json(containers())
                return
            m = re.fullmatch(r"/api/stacks/([^/]+)/compose", u.path)
            if m:
                d = safe_stack(m.group(1)); p = compose_file(d)
                if not p: raise FileNotFoundError("compose")
                self.send_json({"name": p.name, "content": p.read_text(encoding="utf-8")})
                return
            m = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/logs", u.path)
            if m:
                self.send_json({"logs": container_logs(m.group(1))})
                return
            if u.path == "/health":
                runtime()
                self.send_json({"ok": True})
                return
            self.send_static(u.path)
        except FileNotFoundError:
            self.send_json({"error": "not found"}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def do_POST(self):
        try:
            u = urlparse(self.path)
            m = re.fullmatch(r"/api/stacks/([^/]+)/(start|stop|restart|pull)", u.path)
            if m:
                result = run_stack_action(m.group(1), m.group(2))
                self.send_json(result, 200 if result["ok"] else 500)
                return
            m = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/(start|stop|restart)", u.path)
            if m:
                self.send_json(container_action(m.group(1), m.group(2)))
                return
            self.send_json({"error": "not found"}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def do_PUT(self):
        try:
            u = urlparse(self.path)
            m = re.fullmatch(r"/api/stacks/([^/]+)/compose", u.path)
            if not m:
                self.send_json({"error": "not found"}, 404); return
            d = safe_stack(m.group(1)); p = compose_file(d)
            if not p: raise FileNotFoundError("compose")
            payload = self.read_json()
            content = payload.get("content")
            if not isinstance(content, str) or len(content.encode()) > 1_000_000:
                raise ValueError("invalid compose content")
            backup = p.with_suffix(p.suffix + f".rogueforge-{int(time.time())}.bak")
            backup.write_bytes(p.read_bytes())
            p.write_text(content, encoding="utf-8")
            # Validate without applying.
            proc = subprocess.run(compose_command(m.group(1), ["config"]), cwd=d, text=True, capture_output=True, timeout=60)
            if proc.returncode:
                p.write_bytes(backup.read_bytes())
                raise RuntimeError("compose validation failed; original restored\n" + (proc.stdout + proc.stderr)[-10000:])
            self.send_json({"ok": True, "backup": backup.name})
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)


def main():
    runtime()  # Fail early if no engine exists.
    server = ThreadingHTTPServer((BIND, PORT), Handler)
    print(f"RogueForge {VERSION} listening on http://{BIND}:{PORT} ({runtime()['engine']})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
