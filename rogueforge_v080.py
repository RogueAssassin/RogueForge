#!/usr/bin/env python3
"""RogueForge v0.8.0 stack-first runtime.

Adds stack update and .env management over the flexible v0.7.1 discovery/runtime
layers while retaining live logs, terminal, bulk runtime controls and auth.
"""
from __future__ import annotations

import re
import time
from urllib.parse import urlparse

import rogueforge as core
import rogueforge_v071  # installs 0.7.1 discovery + live operation handlers

VERSION = "0.8.0"
core.VERSION = VERSION
core.Handler.server_version = f"RogueForge/{VERSION}"
_previous_get = core.Handler.do_GET
_previous_post = core.Handler.do_POST
_previous_put = core.Handler.do_PUT


def stack_env_path(name: str):
    directory = core.safe_stack(name)
    return directory / ".env"


def stack_env(name: str):
    path = stack_env_path(name)
    return {"name": ".env", "exists": path.is_file(), "content": path.read_text(encoding="utf-8") if path.is_file() else ""}


def save_stack_env(name: str, content: str):
    if not isinstance(content, str) or len(content.encode()) > 1_000_000:
        raise ValueError("invalid environment content")
    path = stack_env_path(name)
    backup = None
    if path.is_file():
        backup = path.with_name(f".env.rogueforge-{int(time.time())}.bak")
        backup.write_bytes(path.read_bytes())
    path.write_text(content, encoding="utf-8")
    # Validate interpolation with the exact Compose implementation used by this host.
    try:
        core.run_compose(name, ["config"], timeout=60)
    except Exception:
        if backup and backup.is_file():
            path.write_bytes(backup.read_bytes())
        elif path.is_file():
            path.unlink()
        raise
    return {"ok": True, "backup": backup.name if backup else None}


def update_stack(name: str):
    core.safe_stack(name)
    pull = core.run_compose(name, ["pull"], timeout=900)
    up = core.run_compose(name, ["up", "-d", "--remove-orphans"], timeout=900)
    return {"ok": True, "output": (pull + "\n" + up)[-100_000:]}


def do_GET_v080(self):
    try:
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/stacks/([^/]+)/env", path)
        if match:
            if not self.require_auth():
                return
            self.send_json(stack_env(match.group(1)))
            return
    except FileNotFoundError:
        self.send_json({"error": "not found"}, 404); return
    except PermissionError as exc:
        self.send_json({"error": str(exc)}, 409); return
    except Exception as exc:
        self.send_json({"error": str(exc)}, 500); return
    return _previous_get(self)


def do_POST_v080(self):
    try:
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/stacks/([^/]+)/update", path)
        if match:
            if not self.require_auth(csrf=True):
                return
            self.send_json(update_stack(match.group(1)))
            return
    except PermissionError as exc:
        self.send_json({"error": str(exc)}, 409); return
    except Exception as exc:
        self.send_json({"error": str(exc)}, 500); return
    return _previous_post(self)


def do_PUT_v080(self):
    try:
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/stacks/([^/]+)/env", path)
        if match:
            if not self.require_auth(csrf=True):
                return
            payload = self.read_json()
            self.send_json(save_stack_env(match.group(1), payload.get("content")))
            return
    except PermissionError as exc:
        self.send_json({"error": str(exc)}, 409); return
    except Exception as exc:
        self.send_json({"error": str(exc)}, 500); return
    return _previous_put(self)


core.Handler.do_GET = do_GET_v080
core.Handler.do_POST = do_POST_v080
core.Handler.do_PUT = do_PUT_v080

if __name__ == "__main__":
    core.main()
