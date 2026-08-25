#!/usr/bin/env python3
"""RogueForge v0.7.0 live operations layer.

Adds authenticated live log streaming and interactive container exec sessions on
top of the stable 0.6.2 container-management extension.
"""
from __future__ import annotations

import json
import re
import secrets
import subprocess
import threading
import time
from urllib.parse import parse_qs, urlparse

import rogueforge as core
import rogueforge_ext as base

VERSION = "0.7.0"
core.VERSION = VERSION
core.Handler.server_version = f"RogueForge/{VERSION}"

_previous_get = core.Handler.do_GET
_previous_post = core.Handler.do_POST
_previous_delete = getattr(core.Handler, "do_DELETE", None)
_terminal_sessions: dict[str, dict] = {}
_terminal_lock = threading.Lock()
TERMINAL_TTL = 1800
MAX_TERMINAL_CHUNKS = 2500


def _engine_prefix():
    rt = core.runtime()
    if rt["engine"] == "podman":
        podman = core.os.environ.get("ROGUEFORGE_PODMAN", "/usr/bin/podman")
        return [podman, "--remote", "--url", f"unix://{rt['socket']}"], core.os.environ.copy()
    env = core.os.environ.copy()
    env["DOCKER_HOST"] = f"unix://{rt['socket']}"
    return ["/usr/bin/docker"], env


def _popen_engine(args: list[str], *, stdin=False):
    prefix, env = _engine_prefix()
    return subprocess.Popen(
        prefix + args,
        env=env,
        stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def _cleanup_terminals():
    now = time.time()
    stale = []
    with _terminal_lock:
        for token, session in _terminal_sessions.items():
            proc = session["process"]
            if now - session["lastAccess"] > TERMINAL_TTL or proc.poll() is not None:
                stale.append(token)
    for token in stale:
        close_terminal(token)


def _terminal_reader(token: str):
    with _terminal_lock:
        session = _terminal_sessions.get(token)
    if not session:
        return
    proc = session["process"]
    try:
        while True:
            line = proc.stdout.readline() if proc.stdout else ""
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            with _terminal_lock:
                current = _terminal_sessions.get(token)
                if not current:
                    break
                current["chunks"].append(line)
                if len(current["chunks"]) > MAX_TERMINAL_CHUNKS:
                    trim = len(current["chunks"]) - MAX_TERMINAL_CHUNKS
                    del current["chunks"][:trim]
                    current["baseCursor"] += trim
    finally:
        with _terminal_lock:
            current = _terminal_sessions.get(token)
            if current:
                current["closed"] = True
                current["exitCode"] = proc.poll()


def start_terminal(cid: str):
    _cleanup_terminals()
    meta = base._container_meta(cid)
    inspect = base.inspect_container(cid)
    if not inspect.get("running"):
        raise RuntimeError("Container must be running before opening a terminal")
    shell = "/bin/sh"
    try:
        probe = base.engine_cli(["exec", meta["id"], "sh", "-lc", "command -v bash || command -v sh"], timeout=30).strip().splitlines()
        if probe:
            shell = probe[-1].strip() or shell
    except Exception:
        pass
    proc = _popen_engine(["exec", "-i", meta["id"], shell], stdin=True)
    token = secrets.token_urlsafe(24)
    session = {
        "token": token,
        "containerId": meta["id"],
        "containerName": meta["name"],
        "shell": shell,
        "process": proc,
        "chunks": [],
        "baseCursor": 0,
        "created": time.time(),
        "lastAccess": time.time(),
        "closed": False,
        "exitCode": None,
    }
    with _terminal_lock:
        _terminal_sessions[token] = session
    threading.Thread(target=_terminal_reader, args=(token,), daemon=True).start()
    return {"ok": True, "token": token, "container": meta["name"], "shell": shell, "cursor": 0}


def terminal_output(token: str, cursor: int):
    _cleanup_terminals()
    with _terminal_lock:
        session = _terminal_sessions.get(token)
        if not session:
            raise FileNotFoundError("terminal session")
        session["lastAccess"] = time.time()
        base_cursor = session["baseCursor"]
        start = max(0, cursor - base_cursor)
        chunks = session["chunks"][start:]
        next_cursor = base_cursor + len(session["chunks"])
        return {
            "output": "".join(chunks),
            "cursor": next_cursor,
            "closed": session["closed"],
            "exitCode": session["exitCode"],
            "container": session["containerName"],
            "shell": session["shell"],
        }


def terminal_input(token: str, value: str):
    if not isinstance(value, str) or len(value.encode()) > 8192:
        raise ValueError("terminal input is too large")
    with _terminal_lock:
        session = _terminal_sessions.get(token)
        if not session:
            raise FileNotFoundError("terminal session")
        session["lastAccess"] = time.time()
        proc = session["process"]
    if proc.poll() is not None or not proc.stdin:
        raise RuntimeError("terminal session is closed")
    proc.stdin.write(value)
    proc.stdin.flush()
    return {"ok": True}


def close_terminal(token: str):
    with _terminal_lock:
        session = _terminal_sessions.pop(token, None)
    if not session:
        return {"ok": True}
    proc = session["process"]
    try:
        if proc.stdin:
            proc.stdin.close()
    except Exception:
        pass
    if proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    return {"ok": True}


def stream_logs(handler, cid: str):
    meta = base._container_meta(cid)
    proc = _popen_engine(["logs", "--follow", "--tail", "150", "--timestamps", meta["id"]])
    handler.send_response(200)
    handler.send_header("content-type", "text/event-stream")
    handler.send_header("cache-control", "no-cache, no-store")
    handler.send_header("connection", "keep-alive")
    handler.send_header("x-accel-buffering", "no")
    handler.end_headers()
    try:
        handler.wfile.write(b"event: ready\ndata: {}\n\n")
        handler.wfile.flush()
        while True:
            line = proc.stdout.readline() if proc.stdout else ""
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            payload = json.dumps({"line": line.rstrip("\n")}).encode()
            handler.wfile.write(b"data: " + payload + b"\n\n")
            handler.wfile.flush()
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        if proc.poll() is None:
            proc.terminate()


def do_GET_v070(self):
    try:
        parsed = urlparse(self.path)
        path = parsed.path
        match = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/logs/stream", path)
        if match:
            if not self.require_auth():
                return
            stream_logs(self, match.group(1))
            return
        match = re.fullmatch(r"/api/terminal/([A-Za-z0-9_-]+)", path)
        if match:
            if not self.require_auth():
                return
            query = parse_qs(parsed.query)
            try:
                cursor = max(0, int((query.get("cursor") or ["0"])[0]))
            except ValueError:
                cursor = 0
            self.send_json(terminal_output(match.group(1), cursor))
            return
    except FileNotFoundError:
        self.send_json({"error": "not found"}, 404)
        return
    except Exception as exc:
        self.send_json({"error": str(exc)}, 500)
        return
    return _previous_get(self)


def do_POST_v070(self):
    try:
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/terminal", path)
        if match:
            if not self.require_auth(csrf=True):
                return
            self.send_json(start_terminal(match.group(1)))
            return
        match = re.fullmatch(r"/api/terminal/([A-Za-z0-9_-]+)/input", path)
        if match:
            if not self.require_auth(csrf=True):
                return
            payload = self.read_json()
            self.send_json(terminal_input(match.group(1), payload.get("input", "")))
            return
    except FileNotFoundError:
        self.send_json({"error": "not found"}, 404)
        return
    except Exception as exc:
        self.send_json({"error": str(exc)}, 500)
        return
    return _previous_post(self)


def do_DELETE_v070(self):
    try:
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/terminal/([A-Za-z0-9_-]+)", path)
        if match:
            if not self.require_auth(csrf=True):
                return
            self.send_json(close_terminal(match.group(1)))
            return
        self.send_json({"error": "not found"}, 404)
    except Exception as exc:
        self.send_json({"error": str(exc)}, 500)


core.Handler.do_GET = do_GET_v070
core.Handler.do_POST = do_POST_v070
core.Handler.do_DELETE = do_DELETE_v070

if __name__ == "__main__":
    core.main()
