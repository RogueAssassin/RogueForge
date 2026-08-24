#!/usr/bin/env python3
from __future__ import annotations

import base64
from http.cookies import SimpleCookie
from http import HTTPStatus
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hashlib
import hmac
import mimetypes
import os
from pathlib import Path
try:
    import pwd
except ImportError:  # Development and tests may run on Windows.
    pwd = None
import re
import secrets
import socket
import subprocess
import sys
import time
import threading
from urllib.parse import parse_qs, unquote, urlparse

VERSION = "0.4.1"
PORT = int(os.environ.get("ROGUEFORGE_PORT", "7810"))
BIND = os.environ.get("ROGUEFORGE_BIND", "127.0.0.1")
STACKS_DIR = Path(os.environ.get("ROGUEFORGE_STACKS_DIR", "/opt/stacks")).resolve()
STATIC_DIR = Path(os.environ.get("ROGUEFORGE_STATIC_DIR", Path(__file__).with_name("static"))).resolve()
ENGINE = os.environ.get("ROGUEFORGE_ENGINE", "auto").strip().lower()
SOCKET_PATH = os.environ.get("ROGUEFORGE_SOCKET", "").strip()
PODMAN_USER = os.environ.get("ROGUEFORGE_PODMAN_USER", "").strip()
PODMAN_REMOTE = os.environ.get("ROGUEFORGE_PODMAN_REMOTE", "").strip().lower() in ("1", "true", "yes")
PUBLIC_URL = os.environ.get("ROGUEFORGE_PUBLIC_URL", "").strip()
ICONS_DIR = Path(os.environ.get("ROGUEFORGE_ICONS_DIR", "/opt/media-server/rogue-dashboard/app/static/icons")).resolve()
AUTH_FILE = Path(os.environ.get("ROGUEFORGE_AUTH_FILE", Path(__file__).with_name("data") / "auth.json")).resolve()
SESSION_TTL = int(os.environ.get("ROGUEFORGE_SESSION_TTL", "43200"))
DEMO_MODE = os.environ.get("ROGUEFORGE_DEMO", "").strip().lower() in ("1", "true", "yes")
MAX_BODY = 2_000_000
STACK_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
COMPOSE_NAMES = ("podman-compose.yaml", "compose.podman.yaml", "docker-compose.yaml", "docker-compose.yml", "compose.yaml", "compose.yml")
ICON_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,255}$")
ICON_EXTENSIONS = (".svg", ".png", ".webp", ".jpg", ".jpeg")
LOGIN_WINDOW = 300
LOGIN_LIMIT = 8
_login_attempts = {}
_login_lock = threading.Lock()


def b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def load_auth():
    if not AUTH_FILE.is_file():
        return None
    try:
        data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        required = ("username", "salt", "passwordHash", "iterations", "sessionSecret")
        return data if all(data.get(key) for key in required) else None
    except (OSError, json.JSONDecodeError):
        return None


def verify_password(password: str, auth) -> bool:
    if not isinstance(password, str) or len(password) > 1024:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), b64decode(auth["salt"]), int(auth["iterations"]))
    return hmac.compare_digest(b64encode(candidate), auth["passwordHash"])


def make_session(auth):
    payload = {"user": auth["username"], "exp": int(time.time()) + SESSION_TTL, "csrf": secrets.token_urlsafe(24)}
    encoded = b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = b64encode(hmac.new(b64decode(auth["sessionSecret"]), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}", payload


def read_session(token: str, auth):
    try:
        encoded, signature = token.split(".", 1)
        expected = b64encode(hmac.new(b64decode(auth["sessionSecret"]), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(b64decode(encoded))
        if payload.get("user") != auth["username"] or int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def login_allowed(client: str, success: bool | None = None) -> bool:
    now = time.time()
    with _login_lock:
        recent = [stamp for stamp in _login_attempts.get(client, []) if now - stamp < LOGIN_WINDOW]
        if success is True:
            _login_attempts.pop(client, None)
            return True
        if success is False:
            recent.append(now)
            _login_attempts[client] = recent
        return len(recent) < LOGIN_LIMIT


class UnixHTTPConnection(HTTPConnection):
    def __init__(self, path: str):
        super().__init__("localhost", timeout=5)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.path)


def request_socket(socket_path: str, method: str, path: str, body: bytes | None = None, maximum: int = 5_000_000):
    conn = UnixHTTPConnection(socket_path)
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


def request_engine(method: str, path: str, body: bytes | None = None, maximum: int = 5_000_000):
    return request_socket(runtime()["socket"], method, path, body, maximum)


_runtime = None
def runtime():
    global _runtime
    if _runtime:
        return _runtime
    if DEMO_MODE:
        _runtime = {"engine": "demo", "socket": "simulated", "version": "26.1.0", "apiVersion": "1.45"}
        return _runtime
    candidates = []
    if SOCKET_PATH:
        candidates.append(SOCKET_PATH)
    if PODMAN_USER and pwd:
        try:
            candidates.append(f"/run/user/{pwd.getpwnam(PODMAN_USER).pw_uid}/podman/podman.sock")
        except KeyError:
            pass
    run_user = Path("/run/user")
    if run_user.is_dir():
        candidates.extend(str(path) for path in sorted(run_user.glob("*/podman/podman.sock")))
    candidates += ["/run/podman/podman.sock", "/var/run/docker.sock"]
    candidates = list(dict.fromkeys(candidates))
    for p in candidates:
        if not p or not Path(p).exists():
            continue
        try:
            data = request_socket(p, "GET", "/version", maximum=200_000) or {}
            blob = json.dumps(data).lower()
            kind = "podman" if ("podman" in blob or "libpod" in blob) else "docker"
            if ENGINE not in ("auto", kind):
                continue
            _runtime = {
                "engine": kind,
                "socket": p,
                "version": str(data.get("Version") or data.get("version") or "unknown"),
                "apiVersion": str(data.get("ApiVersion") or data.get("APIVersion") or "unknown"),
                "context": "remote socket" if PODMAN_REMOTE else ("rootless" if p.startswith("/run/user/") else "rootful"),
                "podmanUser": PODMAN_USER or None,
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


def normalize_icon_key(value: str) -> str:
    value = value.lower().split("@", 1)[0].split(":", 1)[0].rstrip("/")
    value = value.rsplit("/", 1)[-1]
    for suffix in ("-server", "-web", "-app", "_server", "_web", "_app"):
        if value.endswith(suffix):
            value = value[:-len(suffix)]
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def resolve_icon(key: str) -> Path | None:
    if not ICON_KEY.fullmatch(key) or not ICONS_DIR.is_dir():
        return None
    wanted = normalize_icon_key(unquote(key))
    if not wanted:
        return None
    for path in ICONS_DIR.iterdir():
        if path.is_file() and path.suffix.lower() in ICON_EXTENSIONS and normalize_icon_key(path.stem) == wanted:
            return path
    return None


def discover_stacks():
    projects = {}
    for container in containers():
        projects.setdefault(container.get("project", "standalone"), []).append(container)
    result = []
    if not STACKS_DIR.is_dir():
        return result
    for p in sorted(STACKS_DIR.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        cf = compose_file(p)
        if not cf:
            continue
        members = projects.get(p.name, [])
        running = sum(item["state"] == "running" for item in members)
        result.append({
            "name": p.name,
            "composeFile": cf.name,
            "hasEnv": (p / ".env").is_file(),
            "engineHint": "podman" if "podman" in cf.name else ("docker" if "docker" in cf.name else "portable"),
            "services": len(members),
            "running": running,
            "state": "running" if members and running == len(members) else ("partial" if running else "stopped"),
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
        if PODMAN_USER:
            try:
                account = pwd.getpwnam(PODMAN_USER)
                uid = account.pw_uid
            except KeyError as exc:
                raise RuntimeError(f"configured Podman user does not exist: {PODMAN_USER}") from exc
            cmd = ["/usr/sbin/runuser", "-u", PODMAN_USER, "--", "env", f"HOME={account.pw_dir}", f"USER={PODMAN_USER}", f"LOGNAME={PODMAN_USER}", f"XDG_RUNTIME_DIR=/run/user/{uid}", binary]
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


def podman_user_command(args: list[str], timeout: int = 60):
    """Run Podman inside the configured rootless user's storage context."""
    if not PODMAN_USER or not pwd:
        raise RuntimeError("no rootless Podman user is configured")
    try:
        account = pwd.getpwnam(PODMAN_USER)
        uid = account.pw_uid
    except KeyError as exc:
        raise RuntimeError(f"configured Podman user does not exist: {PODMAN_USER}") from exc
    podman = os.environ.get("ROGUEFORGE_PODMAN", "/usr/bin/podman")
    command = ["/usr/sbin/runuser", "-u", PODMAN_USER, "--", "env", f"HOME={account.pw_dir}", f"USER={PODMAN_USER}", f"LOGNAME={PODMAN_USER}", f"XDG_RUNTIME_DIR=/run/user/{uid}", podman] + args
    process = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    if process.returncode:
        raise RuntimeError((process.stdout + process.stderr)[-10_000:] or "Podman command failed")
    return process.stdout


def podman_remote_command(args: list[str], timeout: int = 60):
    podman = os.environ.get("ROGUEFORGE_PODMAN", "/usr/bin/podman")
    command = [podman, "--remote", "--url", f"unix://{runtime()['socket']}"] + args
    process = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    if process.returncode:
        raise RuntimeError((process.stdout + process.stderr)[-10_000:] or "Remote Podman command failed")
    return process.stdout


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
    if DEMO_MODE:
        return {"ok": True, "output": f"Demo mode: {action} completed for {stack}."}
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
    raw = [
        {"Id": "a1b2c3d4e5f600000000000000000001", "Names": ["/immich-server"], "Image": "ghcr.io/immich-app/immich-server:release", "State": "running", "Status": "Up 8 days (healthy)", "Labels": {"com.docker.compose.project": "immich"}, "Ports": [{"PrivatePort": 2283, "PublicPort": 2283, "Type": "tcp"}]},
        {"Id": "b2c3d4e5f6a700000000000000000002", "Names": ["/immich-postgres"], "Image": "tensorchord/pgvecto-rs:pg14-v0.2.0", "State": "running", "Status": "Up 8 days (healthy)", "Labels": {"com.docker.compose.project": "immich"}, "Ports": []},
        {"Id": "c3d4e5f6a7b800000000000000000003", "Names": ["/jellyfin"], "Image": "jellyfin/jellyfin:latest", "State": "running", "Status": "Up 3 days", "Labels": {"com.docker.compose.project": "media"}, "Ports": [{"PrivatePort": 8096, "PublicPort": 8096, "Type": "tcp"}]},
        {"Id": "d4e5f6a7b8c900000000000000000004", "Names": ["/paperless-web"], "Image": "ghcr.io/paperless-ngx/paperless-ngx:latest", "State": "exited", "Status": "Exited (1) 26 minutes ago", "Labels": {"com.docker.compose.project": "paperless"}, "Ports": []},
    ] if DEMO_MODE else load_containers()
    result = []
    for item in raw or []:
        names = item.get("Names") or []
        if isinstance(names, str):
            names = [names]
        labels = item.get("Labels") or {}
        project = (labels.get("com.docker.compose.project") or labels.get("io.podman.compose.project")
                   or labels.get("com.docker.compose.project.working_dir") or "standalone")
        result.append({
            "id": str(item.get("Id") or item.get("ID") or "")[:12],
            "name": (names[0].lstrip("/") if names else "unnamed"),
            "image": item.get("Image") or item.get("ImageName") or "unknown",
            "state": str(item.get("State", "unknown")).lower(),
            "status": item.get("Status", "unknown"),
            "ports": item.get("Ports") or [],
            "project": Path(project).name if "/" in project else project,
        })
    return sorted(result, key=lambda x: (x["state"] != "running", x["name"].lower()))


def load_containers():
    """Use the owner's CLI for rootless Podman, retaining the API as fallback."""
    if runtime()["engine"] == "podman" and PODMAN_USER:
        try:
            data = json.loads(podman_user_command(["ps", "-a", "--format", "json"], timeout=30) or "[]")
            if isinstance(data, list):
                return data
        except Exception as exc:
            sys.stderr.write(f"rootless Podman CLI inventory failed; using API fallback: {exc}\n")
    if runtime()["engine"] == "podman" and PODMAN_REMOTE:
        try:
            data = json.loads(podman_remote_command(["ps", "-a", "--format", "json"], timeout=30) or "[]")
            if isinstance(data, list):
                return data
        except Exception as exc:
            sys.stderr.write(f"remote Podman CLI inventory failed; using API fallback: {exc}\n")
    return engine_containers()


def engine_containers():
    """Prefer Podman's native API, then fall back to the Docker-compatible API."""
    rt = runtime()
    if rt["engine"] == "podman":
        version = rt["version"].split("-")[0]
        api_version = rt["apiVersion"]
        endpoints = [
            f"/v{version}/libpod/containers/json?all=true",
            f"/v{api_version}/libpod/containers/json?all=true",
            "/libpod/containers/json?all=true",
            "/containers/json?all=1",
        ]
    else:
        endpoints = ["/containers/json?all=1"]
    errors = []
    for endpoint in endpoints:
        try:
            data = request_engine("GET", endpoint)
            if data is not None:
                return data
        except Exception as exc:
            errors.append(str(exc))
    raise RuntimeError("Unable to list containers: " + "; ".join(errors))


def container_action(cid: str, action: str):
    if not re.fullmatch(r"[0-9a-fA-F]{12,64}", cid):
        raise ValueError("invalid container id")
    if action not in ("start", "stop", "restart"):
        raise ValueError("unsupported action")
    if not DEMO_MODE and runtime()["engine"] == "podman" and PODMAN_USER:
        podman_user_command([action, "--time", "10", cid] if action in ("stop", "restart") else [action, cid])
    elif not DEMO_MODE and runtime()["engine"] == "podman" and PODMAN_REMOTE:
        podman_remote_command([action, "--time", "10", cid] if action in ("stop", "restart") else [action, cid])
    elif not DEMO_MODE:
        suffix = "?t=10" if action in ("stop", "restart") else ""
        request_engine("POST", f"/containers/{cid}/{action}{suffix}", b"")
    return {"ok": True}


def container_logs(cid: str):
    if not re.fullmatch(r"[0-9a-fA-F]{12,64}", cid):
        raise ValueError("invalid container id")
    if DEMO_MODE:
        return "\n".join(f"2026-08-24T10:{n:02d}:00Z  INFO  demo service heartbeat" for n in range(15))
    if runtime()["engine"] == "podman" and PODMAN_USER:
        return podman_user_command(["logs", "--tail", "250", "--timestamps", cid], timeout=30)
    if runtime()["engine"] == "podman" and PODMAN_REMOTE:
        return podman_remote_command(["logs", "--tail", "250", "--timestamps", cid], timeout=30)
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

    def send_json(self, value, status=200, headers=None):
        raw = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        for name, content in (headers or {}).items():
            self.send_header(name, content)
        self.end_headers()
        self.wfile.write(raw)

    def session_payload(self):
        auth = load_auth()
        if not auth:
            return None
        cookie = SimpleCookie(self.headers.get("cookie", ""))
        morsel = cookie.get("rogueforge_session")
        return read_session(morsel.value, auth) if morsel else None

    def require_auth(self, csrf=False):
        if not load_auth():
            self.send_json({"error": "administrator account is not configured"}, 503)
            return None
        session = self.session_payload()
        if not session:
            self.send_json({"error": "authentication required"}, 401)
            return None
        if csrf and not hmac.compare_digest(self.headers.get("x-csrf-token", ""), session.get("csrf", "")):
            self.send_json({"error": "invalid security token"}, 403)
            return None
        return session

    def session_cookie(self, token, clear=False):
        parts = [f"rogueforge_session={token}", "Path=/", "HttpOnly", "SameSite=Strict"]
        parts.append("Max-Age=0" if clear else f"Max-Age={SESSION_TTL}")
        if PUBLIC_URL.lower().startswith("https://"):
            parts.append("Secure")
        return "; ".join(parts)

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

    def send_icon(self, key):
        path = resolve_icon(key)
        if not path:
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("content-type", mimetypes.guess_type(str(path))[0] or "application/octet-stream")
        self.send_header("content-length", str(len(data)))
        self.send_header("cache-control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        try:
            u = urlparse(self.path)
            if u.path == "/api/auth/session":
                auth = load_auth()
                session = self.session_payload()
                self.send_json({"configured": bool(auth), "authenticated": bool(session), "user": session.get("user") if session else None, "csrf": session.get("csrf") if session else None})
                return
            if u.path == "/api/status":
                session = self.session_payload()
                rt = runtime()
                status = {"appVersion": VERSION, "engine": rt["engine"], "version": rt["version"], "apiVersion": rt["apiVersion"], "context": rt.get("context"), "demo": DEMO_MODE, "publicUrl": PUBLIC_URL, "authConfigured": bool(load_auth())}
                status.update({"socket": rt["socket"], "stacksDir": str(STACKS_DIR), "iconsDir": str(ICONS_DIR)}) if session else status.update({"socket": "Protected", "stacksDir": "Protected", "iconsDir": "Protected"})
                self.send_json(status)
                return
            m = re.fullmatch(r"/api/icons/(.+)", u.path)
            if m:
                self.send_icon(unquote(m.group(1)))
                return
            if u.path == "/api/stacks":
                self.send_json(discover_stacks())
                return
            if u.path == "/api/containers":
                self.send_json(containers())
                return
            m = re.fullmatch(r"/api/stacks/([^/]+)/compose", u.path)
            if m:
                if not self.require_auth(): return
                d = safe_stack(m.group(1)); p = compose_file(d)
                if not p: raise FileNotFoundError("compose")
                self.send_json({"name": p.name, "content": p.read_text(encoding="utf-8")})
                return
            m = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/logs", u.path)
            if m:
                if not self.require_auth(): return
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
            if u.path == "/api/auth/login":
                client = self.client_address[0]
                if not login_allowed(client):
                    self.send_json({"error": "too many login attempts; try again later"}, 429); return
                auth = load_auth()
                if not auth:
                    self.send_json({"error": "administrator account is not configured"}, 503); return
                payload = self.read_json()
                valid = hmac.compare_digest(str(payload.get("username", "")), auth["username"]) and verify_password(payload.get("password", ""), auth)
                if not valid:
                    login_allowed(client, False)
                    time.sleep(0.35)
                    self.send_json({"error": "invalid username or password"}, 401); return
                login_allowed(client, True)
                token, session = make_session(auth)
                self.send_json({"ok": True, "user": session["user"], "csrf": session["csrf"]}, headers={"set-cookie": self.session_cookie(token)})
                return
            if u.path == "/api/auth/logout":
                if not self.require_auth(csrf=True): return
                self.send_json({"ok": True}, headers={"set-cookie": self.session_cookie("", clear=True)})
                return
            m = re.fullmatch(r"/api/stacks/([^/]+)/(start|stop|restart|pull)", u.path)
            if m:
                if not self.require_auth(csrf=True): return
                result = run_stack_action(m.group(1), m.group(2))
                self.send_json(result, 200 if result["ok"] else 500)
                return
            m = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/(start|stop|restart)", u.path)
            if m:
                if not self.require_auth(csrf=True): return
                self.send_json(container_action(m.group(1), m.group(2)))
                return
            self.send_json({"error": "not found"}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def do_PUT(self):
        try:
            u = urlparse(self.path)
            if not self.require_auth(csrf=True): return
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
