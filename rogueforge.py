#!/usr/bin/env python3
from __future__ import annotations

import base64
from http.cookies import SimpleCookie
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import hmac
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import unquote, urlparse

VERSION = "0.5.0"
PORT = int(os.environ.get("ROGUEFORGE_PORT", "7810"))
BIND = os.environ.get("ROGUEFORGE_BIND", "127.0.0.1")
STACKS_DIR = Path(os.environ.get("ROGUEFORGE_STACKS_DIR", "/opt/media-server")).resolve()
STATIC_DIR = Path(os.environ.get("ROGUEFORGE_STATIC_DIR", Path(__file__).with_name("static"))).resolve()
ENGINE = os.environ.get("ROGUEFORGE_ENGINE", "auto").strip().lower()
SOCKET_PATH = os.environ.get("ROGUEFORGE_SOCKET", "").strip()
PODMAN_REMOTE = os.environ.get("ROGUEFORGE_PODMAN_REMOTE", "").strip().lower() in ("1", "true", "yes")
PUBLIC_URL = os.environ.get("ROGUEFORGE_PUBLIC_URL", "").strip()
ICONS_DIR = Path(os.environ.get("ROGUEFORGE_ICONS_DIR", "/opt/media-server/rogue-dashboard/app/static/icons")).resolve()
AUTH_FILE = Path(os.environ.get("ROGUEFORGE_AUTH_FILE", Path(__file__).with_name("data") / "auth.json")).resolve()
SELF_STACK = os.environ.get("ROGUEFORGE_SELF_STACK", "rogueforge").strip()
SESSION_TTL = int(os.environ.get("ROGUEFORGE_SESSION_TTL", "43200"))
DEMO_MODE = os.environ.get("ROGUEFORGE_DEMO", "").strip().lower() in ("1", "true", "yes")
MAX_BODY = 2_000_000
LOGIN_WINDOW = 300
LOGIN_LIMIT = 8
STACK_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
COMPOSE_NAMES = ("podman-compose.yaml", "compose.podman.yaml", "docker-compose.yaml", "docker-compose.yml", "compose.yaml", "compose.yml")
ICON_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,255}$")
ICON_EXTENSIONS = (".svg", ".png", ".webp", ".jpg", ".jpeg")
_login_attempts: dict[str, list[float]] = {}
_login_lock = threading.Lock()
_sessions: dict[str, dict] = {}
_runtime = None


def _b64(data: bytes):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(data: str):
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def load_auth():
    try:
        data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        if not all(data.get(k) for k in ("username", "salt", "passwordHash")):
            return None
        return data
    except Exception:
        return None


def auth_diagnostics():
    exists = AUTH_FILE.is_file()
    readable = os.access(AUTH_FILE, os.R_OK) if exists else False
    auth = load_auth()
    return {"path": str(AUTH_FILE), "exists": exists, "readable": readable, "valid": bool(auth), "username": auth.get("username") if auth else None}


def verify_password(password, auth):
    try:
        salt = _unb64(auth["salt"])
        expected = _unb64(auth["passwordHash"])
        rounds = int(auth.get("iterations", 600_000))
        actual = hashlib.pbkdf2_hmac("sha256", str(password).encode(), salt, rounds)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def make_session(auth):
    token = secrets.token_urlsafe(32)
    session = {"user": auth["username"], "csrf": secrets.token_urlsafe(24), "expires": time.time() + SESSION_TTL}
    _sessions[token] = session
    return token, session


def read_session(token, auth):
    session = _sessions.get(token)
    if not session or session["expires"] < time.time() or session["user"] != auth["username"]:
        _sessions.pop(token, None)
        return None
    session["expires"] = time.time() + SESSION_TTL
    return session


def login_allowed(client, success=None):
    now = time.time()
    with _login_lock:
        recent = [t for t in _login_attempts.get(client, []) if now - t < LOGIN_WINDOW]
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


def runtime():
    global _runtime
    if _runtime:
        return _runtime
    if DEMO_MODE:
        _runtime = {"engine": "demo", "socket": "simulated", "version": "demo", "apiVersion": "demo", "context": "demo"}
        return _runtime
    candidates = [SOCKET_PATH] if SOCKET_PATH else []
    candidates += ["/run/podman/podman.sock", "/var/run/docker.sock"]
    candidates = list(dict.fromkeys(p for p in candidates if p))
    errors = []
    for path in candidates:
        if not Path(path).exists():
            errors.append(f"missing {path}")
            continue
        try:
            data = request_socket(path, "GET", "/version", maximum=200_000) or {}
            blob = json.dumps(data).lower()
            kind = "podman" if ("podman" in blob or "libpod" in blob) else "docker"
            if ENGINE not in ("auto", kind):
                continue
            _runtime = {
                "engine": kind,
                "socket": path,
                "version": str(data.get("Version") or data.get("version") or "unknown"),
                "apiVersion": str(data.get("ApiVersion") or data.get("APIVersion") or "unknown"),
                "context": "remote socket" if kind == "podman" and PODMAN_REMOTE else "socket",
            }
            return _runtime
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    raise RuntimeError("No matching Docker/Podman API socket detected (" + "; ".join(errors) + ")")


def request_engine(method: str, path: str, body: bytes | None = None, maximum: int = 5_000_000):
    return request_socket(runtime()["socket"], method, path, body, maximum)


def compose_file(stack_dir: Path) -> Path | None:
    for name in COMPOSE_NAMES:
        path = stack_dir / name
        if path.is_file():
            return path
    return None


def safe_stack(name: str, allow_self=False) -> Path:
    if not STACK_NAME.fullmatch(name):
        raise ValueError("invalid stack name")
    if name == SELF_STACK and not allow_self:
        raise PermissionError("RogueForge cannot manage its own Compose project from inside itself")
    path = (STACKS_DIR / name).resolve()
    if path.parent != STACKS_DIR:
        raise ValueError("stack path escapes stacks directory")
    if not path.is_dir():
        raise FileNotFoundError(name)
    return path


def normalize_icon_key(value: str) -> str:
    value = value.lower().split("@", 1)[0].split(":", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    for suffix in ("-server", "-web", "-app", "_server", "_web", "_app"):
        if value.endswith(suffix):
            value = value[:-len(suffix)]
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def resolve_icon(key: str) -> Path | None:
    if not ICON_KEY.fullmatch(key) or not ICONS_DIR.is_dir():
        return None
    wanted = normalize_icon_key(unquote(key))
    for path in ICONS_DIR.iterdir():
        if path.is_file() and path.suffix.lower() in ICON_EXTENSIONS and normalize_icon_key(path.stem) == wanted:
            return path
    return None


def podman_remote_env():
    env = os.environ.copy()
    url = f"unix://{runtime()['socket']}"
    env["CONTAINER_HOST"] = url
    env["DOCKER_HOST"] = url
    return env


def podman_remote_command(args: list[str], timeout: int = 60):
    podman = os.environ.get("ROGUEFORGE_PODMAN", "/usr/bin/podman")
    command = [podman, "--remote", "--url", f"unix://{runtime()['socket']}"] + args
    proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    if proc.returncode:
        raise RuntimeError((proc.stdout + proc.stderr)[-20_000:] or "Remote Podman command failed")
    return proc.stdout


def compose_command(stack: str, args: list[str]):
    directory = safe_stack(stack)
    cf = compose_file(directory)
    if not cf:
        raise RuntimeError("compose file not found")
    rt = runtime()
    env = os.environ.copy()
    if rt["engine"] == "podman":
        binary = os.environ.get("ROGUEFORGE_PODMAN_COMPOSE", "/usr/bin/podman-compose")
        if PODMAN_REMOTE:
            env = podman_remote_env()
        # podman-compose 1.x does not support Docker Compose's --env-file global
        # option. It automatically reads .env from cwd, so only pass -f here.
        command = [binary, "-f", str(cf)]
    else:
        binary = os.environ.get("ROGUEFORGE_DOCKER_COMPOSE", "/usr/bin/docker-compose")
        command = [binary]
        env["DOCKER_HOST"] = f"unix://{rt['socket']}"
        if (directory / ".env").is_file():
            command += ["--env-file", str(directory / ".env")]
        command += ["-f", str(cf)]
    command += args
    return directory, command, env


def run_compose(stack: str, args: list[str], timeout=900):
    directory, command, env = compose_command(stack, args)
    proc = subprocess.run(command, cwd=directory, env=env, text=True, capture_output=True, timeout=timeout)
    output = (proc.stdout + proc.stderr)[-100_000:]
    if proc.returncode:
        raise RuntimeError(output or f"Compose command failed ({proc.returncode})")
    return output


def run_stack_action(stack: str, action: str):
    mapping = {"start": ["up", "-d"], "stop": ["stop"], "restart": ["restart"], "pull": ["pull"], "recreate": ["up", "-d", "--force-recreate"]}
    if action not in mapping:
        raise ValueError("unsupported action")
    safe_stack(stack)
    if DEMO_MODE:
        return {"ok": True, "output": f"Demo mode: {action} completed for {stack}."}
    return {"ok": True, "output": run_compose(stack, mapping[action])}


def engine_containers():
    rt = runtime()
    endpoints = ["/containers/json?all=1"]
    if rt["engine"] == "podman":
        version = rt["version"].split("-")[0]
        api_version = rt["apiVersion"]
        endpoints = [f"/v{version}/libpod/containers/json?all=true", f"/v{api_version}/libpod/containers/json?all=true", "/libpod/containers/json?all=true"] + endpoints
    errors = []
    for endpoint in endpoints:
        try:
            data = request_engine("GET", endpoint)
            if data is not None:
                return data
        except Exception as exc:
            errors.append(str(exc))
    raise RuntimeError("Unable to list containers: " + "; ".join(errors))


def load_containers():
    if DEMO_MODE:
        return []
    if runtime()["engine"] == "podman" and PODMAN_REMOTE:
        try:
            data = json.loads(podman_remote_command(["ps", "-a", "--format", "json"], timeout=30) or "[]")
            if isinstance(data, list):
                return data
        except Exception as exc:
            sys.stderr.write(f"remote Podman CLI inventory failed; using API fallback: {exc}\n")
    return engine_containers()


def containers():
    result = []
    for item in load_containers() or []:
        names = item.get("Names") or item.get("names") or []
        if isinstance(names, str): names = [names]
        labels = item.get("Labels") or item.get("labels") or {}
        project = labels.get("com.docker.compose.project") or labels.get("io.podman.compose.project") or labels.get("com.docker.compose.project.working_dir") or "standalone"
        state = item.get("State") or item.get("state") or "unknown"
        result.append({"id": str(item.get("Id") or item.get("ID") or item.get("id") or "")[:12], "name": (names[0].lstrip("/") if names else str(item.get("Name") or "unnamed")), "image": item.get("Image") or item.get("ImageName") or item.get("image") or "unknown", "state": str(state).lower(), "status": item.get("Status") or item.get("status") or str(state), "ports": item.get("Ports") or item.get("ports") or [], "project": Path(str(project)).name if "/" in str(project) else str(project)})
    return sorted(result, key=lambda x: (x["state"] != "running", x["name"].lower()))


def discover_stacks():
    projects = {}
    for container in containers(): projects.setdefault(container.get("project", "standalone"), []).append(container)
    result = []
    if not STACKS_DIR.is_dir(): return result
    for path in sorted(STACKS_DIR.iterdir(), key=lambda x: x.name.lower()):
        if not path.is_dir() or path.name.startswith("."): continue
        cf = compose_file(path)
        if not cf: continue
        members = projects.get(path.name, [])
        running = sum(item["state"] == "running" for item in members)
        result.append({"name": path.name, "composeFile": cf.name, "hasEnv": (path / ".env").is_file(), "engineHint": "podman" if "podman" in cf.name else ("docker" if "docker" in cf.name else "portable"), "services": len(members), "running": running, "state": "running" if members and running == len(members) else ("partial" if running else "stopped"), "managed": path.name != SELF_STACK})
    return result


def container_action(cid: str, action: str):
    if not re.fullmatch(r"[0-9a-fA-F]{12,64}", cid): raise ValueError("invalid container id")
    if action not in ("start", "stop", "restart"): raise ValueError("unsupported action")
    if DEMO_MODE: return {"ok": True}
    if runtime()["engine"] == "podman" and PODMAN_REMOTE:
        args = [action, "--time", "10", cid] if action in ("stop", "restart") else [action, cid]
        podman_remote_command(args)
    else:
        suffix = "?t=10" if action in ("stop", "restart") else ""
        request_engine("POST", f"/containers/{cid}/{action}{suffix}", b"")
    return {"ok": True}


def container_logs(cid: str):
    if not re.fullmatch(r"[0-9a-fA-F]{12,64}", cid): raise ValueError("invalid container id")
    if runtime()["engine"] == "podman" and PODMAN_REMOTE: return podman_remote_command(["logs", "--tail", "250", "--timestamps", cid], timeout=30)
    data = request_engine("GET", f"/containers/{cid}/logs?stdout=1&stderr=1&tail=250&timestamps=1", maximum=2_000_000)
    return data.decode(errors="replace") if isinstance(data, bytes) else (data if isinstance(data, str) else json.dumps(data, indent=2))


def diagnostics():
    rt = runtime()
    checks = {"auth": auth_diagnostics(), "runtime": {"engine": rt["engine"], "socket": rt["socket"], "socketExists": Path(rt["socket"]).exists(), "context": rt.get("context")}, "stacks": {"path": str(STACKS_DIR), "exists": STACKS_DIR.is_dir(), "readable": os.access(STACKS_DIR, os.R_OK), "selfStack": SELF_STACK}, "icons": {"path": str(ICONS_DIR), "exists": ICONS_DIR.is_dir()}}
    if rt["engine"] == "podman" and PODMAN_REMOTE:
        try: checks["runtime"]["remoteCli"] = bool(podman_remote_command(["info", "--format", "json"], timeout=20))
        except Exception as exc: checks["runtime"].update({"remoteCli": False, "remoteCliError": str(exc)})
    return checks


class Handler(BaseHTTPRequestHandler):
    server_version = f"RogueForge/{VERSION}"
    def log_message(self, fmt, *args): sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))
    def send_json(self, value, status=200, headers=None):
        raw = json.dumps(value, separators=(",", ":")).encode(); self.send_response(status); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(raw))); self.send_header("cache-control", "no-store"); self.send_header("x-content-type-options", "nosniff")
        for name, content in (headers or {}).items(): self.send_header(name, content)
        self.end_headers(); self.wfile.write(raw)
    def session_payload(self):
        auth = load_auth()
        if not auth: return None
        cookie = SimpleCookie(self.headers.get("cookie", "")); morsel = cookie.get("rogueforge_session")
        return read_session(morsel.value, auth) if morsel else None
    def require_auth(self, csrf=False):
        if not load_auth(): self.send_json({"error": "administrator account is not configured", "auth": auth_diagnostics()}, 503); return None
        session = self.session_payload()
        if not session: self.send_json({"error": "authentication required"}, 401); return None
        if csrf and not hmac.compare_digest(self.headers.get("x-csrf-token", ""), session.get("csrf", "")): self.send_json({"error": "invalid security token"}, 403); return None
        return session
    def session_cookie(self, token, clear=False):
        parts = [f"rogueforge_session={token}", "Path=/", "HttpOnly", "SameSite=Strict", "Max-Age=0" if clear else f"Max-Age={SESSION_TTL}"]
        if self.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower() == "https": parts.append("Secure")
        return "; ".join(parts)
    def read_json(self):
        length = int(self.headers.get("content-length", "0") or 0)
        if length > MAX_BODY: raise ValueError("request body too large")
        return json.loads(self.rfile.read(length) or b"{}")
    def send_static(self, rel):
        rel = "index.html" if rel in ("", "/") else rel.lstrip("/"); path = (STATIC_DIR / rel).resolve()
        if STATIC_DIR not in path.parents and path != STATIC_DIR: self.send_error(404); return
        if not path.is_file(): path = STATIC_DIR / "index.html"
        data = path.read_bytes(); self.send_response(200); self.send_header("content-type", mimetypes.guess_type(str(path))[0] or "application/octet-stream"); self.send_header("content-length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def send_icon(self, key):
        path = resolve_icon(key)
        if not path: self.send_error(404); return
        data = path.read_bytes(); self.send_response(200); self.send_header("content-type", mimetypes.guess_type(str(path))[0] or "application/octet-stream"); self.send_header("content-length", str(len(data))); self.send_header("cache-control", "public, max-age=3600"); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        try:
            u = urlparse(self.path)
            if u.path == "/api/auth/session":
                auth = load_auth(); session = self.session_payload(); self.send_json({"configured": bool(auth), "authenticated": bool(session), "user": session.get("user") if session else None, "csrf": session.get("csrf") if session else None, "auth": auth_diagnostics()}); return
            if u.path == "/api/status":
                rt = runtime(); session = self.session_payload(); status = {"appVersion": VERSION, "engine": rt["engine"], "version": rt["version"], "apiVersion": rt["apiVersion"], "context": rt.get("context"), "demo": DEMO_MODE, "publicUrl": PUBLIC_URL, "authConfigured": bool(load_auth())}; status.update({"socket": rt["socket"], "stacksDir": str(STACKS_DIR), "iconsDir": str(ICONS_DIR)}) if session else status.update({"socket": "Protected", "stacksDir": "Protected", "iconsDir": "Protected"}); self.send_json(status); return
            if u.path == "/api/stacks": self.send_json(discover_stacks()); return
            if u.path == "/api/containers": self.send_json(containers()); return
            if u.path == "/api/diagnostics":
                if not self.require_auth(): return
                self.send_json(diagnostics()); return
            if u.path == "/health": runtime(); self.send_json({"ok": True, "version": VERSION}); return
            m = re.fullmatch(r"/api/icons/(.+)", u.path)
            if m: self.send_icon(unquote(m.group(1))); return
            m = re.fullmatch(r"/api/stacks/([^/]+)/compose", u.path)
            if m:
                if not self.require_auth(): return
                d = safe_stack(m.group(1)); p = compose_file(d)
                if not p: raise FileNotFoundError("compose")
                self.send_json({"name": p.name, "content": p.read_text(encoding="utf-8")}); return
            m = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/logs", u.path)
            if m:
                if not self.require_auth(): return
                self.send_json({"logs": container_logs(m.group(1))}); return
            self.send_static(u.path)
        except FileNotFoundError: self.send_json({"error": "not found"}, 404)
        except PermissionError as exc: self.send_json({"error": str(exc)}, 409)
        except Exception as exc: self.send_json({"error": str(exc)}, 500)
    def do_POST(self):
        try:
            u = urlparse(self.path)
            if u.path == "/api/auth/login":
                client = self.client_address[0]
                if not login_allowed(client): self.send_json({"error": "too many login attempts; try again later"}, 429); return
                auth = load_auth()
                if not auth: self.send_json({"error": "administrator account is not configured", "auth": auth_diagnostics()}, 503); return
                payload = self.read_json(); valid = hmac.compare_digest(str(payload.get("username", "")), auth["username"]) and verify_password(payload.get("password", ""), auth)
                if not valid: login_allowed(client, False); time.sleep(0.35); self.send_json({"error": "invalid username or password"}, 401); return
                login_allowed(client, True); token, session = make_session(auth); self.send_json({"ok": True, "user": session["user"], "csrf": session["csrf"]}, headers={"set-cookie": self.session_cookie(token)}); return
            if u.path == "/api/auth/logout":
                if not self.require_auth(csrf=True): return
                self.send_json({"ok": True}, headers={"set-cookie": self.session_cookie("", clear=True)}); return
            m = re.fullmatch(r"/api/stacks/([^/]+)/(start|stop|restart|pull|recreate)", u.path)
            if m:
                if not self.require_auth(csrf=True): return
                self.send_json(run_stack_action(m.group(1), m.group(2))); return
            m = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/(start|stop|restart)", u.path)
            if m:
                if not self.require_auth(csrf=True): return
                self.send_json(container_action(m.group(1), m.group(2))); return
            self.send_json({"error": "not found"}, 404)
        except PermissionError as exc: self.send_json({"error": str(exc)}, 409)
        except Exception as exc: self.send_json({"error": str(exc)}, 500)
    def do_PUT(self):
        try:
            u = urlparse(self.path)
            if not self.require_auth(csrf=True): return
            m = re.fullmatch(r"/api/stacks/([^/]+)/compose", u.path)
            if not m: self.send_json({"error": "not found"}, 404); return
            d = safe_stack(m.group(1)); p = compose_file(d)
            if not p: raise FileNotFoundError("compose")
            content = self.read_json().get("content")
            if not isinstance(content, str) or len(content.encode()) > 1_000_000: raise ValueError("invalid compose content")
            backup = p.with_suffix(p.suffix + f".rogueforge-{int(time.time())}.bak"); backup.write_bytes(p.read_bytes()); p.write_text(content, encoding="utf-8")
            try: run_compose(m.group(1), ["config"], timeout=60)
            except Exception: p.write_bytes(backup.read_bytes()); raise
            self.send_json({"ok": True, "backup": backup.name})
        except PermissionError as exc: self.send_json({"error": str(exc)}, 409)
        except Exception as exc: self.send_json({"error": str(exc)}, 500)


def main():
    rt = runtime(); auth_info = auth_diagnostics()
    if not auth_info["valid"]: sys.stderr.write(f"WARNING: authentication is not ready: {auth_info}\n")
    server = ThreadingHTTPServer((BIND, PORT), Handler); print(f"RogueForge {VERSION} listening on http://{BIND}:{PORT} ({rt['engine']}, {rt.get('context')})")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == "__main__": main()
