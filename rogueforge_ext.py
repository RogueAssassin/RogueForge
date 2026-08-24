#!/usr/bin/env python3
"""RogueForge v0.6.0 container-management extension.

Keeps the stable 0.5.x core intact while adding Dockge-style per-container
controls that operate through the already-configured Docker/Podman socket.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlparse

import rogueforge as core

VERSION = "0.6.0"
core.VERSION = VERSION
core.Handler.server_version = f"RogueForge/{VERSION}"

_original_containers = core.containers
_original_get = core.Handler.do_GET
_original_post = core.Handler.do_POST


def _raw_container(cid: str):
    wanted = cid.lower()
    for item in core.load_containers() or []:
        actual = str(item.get("Id") or item.get("ID") or item.get("id") or "")
        if actual.lower().startswith(wanted):
            return item
    raise FileNotFoundError("container")


def _container_meta(cid: str):
    item = _raw_container(cid)
    labels = item.get("Labels") or item.get("labels") or {}
    if not isinstance(labels, dict):
        labels = {}
    names = item.get("Names") or item.get("names") or []
    if isinstance(names, str):
        names = [names]
    name = names[0].lstrip("/") if names else str(item.get("Name") or item.get("name") or "unnamed")
    project = labels.get("com.docker.compose.project") or labels.get("io.podman.compose.project") or "standalone"
    service = labels.get("com.docker.compose.service") or labels.get("io.podman.compose.service") or ""
    image = item.get("Image") or item.get("ImageName") or item.get("image") or "unknown"
    full_id = str(item.get("Id") or item.get("ID") or item.get("id") or cid)
    self_protected = name == core.SELF_STACK or str(project) == core.SELF_STACK
    return {
        "id": full_id,
        "shortId": full_id[:12],
        "name": name,
        "image": image,
        "project": str(project),
        "service": str(service),
        "composeManaged": bool(service and project and project != "standalone"),
        "selfProtected": self_protected,
        "labels": labels,
    }


def containers_v060():
    base = _original_containers()
    for container in base:
        try:
            meta = _container_meta(container["id"])
            container.update({
                "service": meta["service"] or None,
                "composeManaged": meta["composeManaged"],
                "selfProtected": meta["selfProtected"],
            })
        except Exception:
            container.update({"service": None, "composeManaged": False, "selfProtected": False})
    return base


core.containers = containers_v060


def _remote_podman(args: list[str], timeout=900):
    return core.podman_remote_command(args, timeout=timeout)


def _docker_cli(args: list[str], timeout=900):
    import subprocess
    env = core.os.environ.copy()
    env["DOCKER_HOST"] = f"unix://{core.runtime()['socket']}"
    proc = subprocess.run(["/usr/bin/docker"] + args, env=env, text=True, capture_output=True, timeout=timeout)
    output = (proc.stdout + proc.stderr)[-100_000:]
    if proc.returncode:
        raise RuntimeError(output or "Docker command failed")
    return output


def engine_cli(args: list[str], timeout=900):
    rt = core.runtime()
    if rt["engine"] == "podman":
        return _remote_podman(args, timeout=timeout)
    return _docker_cli(args, timeout=timeout)


def inspect_container(cid: str):
    meta = _container_meta(cid)
    raw = engine_cli(["inspect", meta["id"]], timeout=60)
    data = json.loads(raw or "[]")
    inspect = data[0] if isinstance(data, list) and data else data
    state = inspect.get("State") or {}
    config = inspect.get("Config") or {}
    network = inspect.get("NetworkSettings") or {}
    mounts = inspect.get("Mounts") or []
    return {
        **{k: meta[k] for k in ("id", "shortId", "name", "image", "project", "service", "composeManaged", "selfProtected")},
        "created": inspect.get("Created"),
        "status": state.get("Status"),
        "running": state.get("Running"),
        "startedAt": state.get("StartedAt"),
        "finishedAt": state.get("FinishedAt"),
        "restartCount": inspect.get("RestartCount", 0),
        "imageId": inspect.get("Image"),
        "command": config.get("Cmd") or [],
        "entrypoint": config.get("Entrypoint") or [],
        "environment": config.get("Env") or [],
        "mounts": [{"source": m.get("Source"), "destination": m.get("Destination"), "type": m.get("Type"), "rw": m.get("RW")} for m in mounts],
        "networks": list((network.get("Networks") or {}).keys()),
    }


def _require_mutable(meta, action):
    if meta["selfProtected"]:
        raise PermissionError(f"RogueForge cannot {action} its own container from inside itself")


def update_container(cid: str):
    meta = _container_meta(cid)
    _require_mutable(meta, "update")
    if not meta["composeManaged"]:
        output = engine_cli(["pull", meta["image"]], timeout=900)
        return {"ok": True, "output": output, "recreated": False, "message": "Image pulled. Standalone containers are not recreated automatically because their original run configuration may not be reproducible."}
    core.safe_stack(meta["project"])
    pull = core.run_compose(meta["project"], ["pull", meta["service"]], timeout=900)
    up = core.run_compose(meta["project"], ["up", "-d", "--no-deps", "--remove-orphans", meta["service"]], timeout=900)
    return {"ok": True, "output": (pull + "\n" + up)[-100_000:], "recreated": True}


def recreate_container(cid: str):
    meta = _container_meta(cid)
    _require_mutable(meta, "recreate")
    if not meta["composeManaged"]:
        raise RuntimeError("Recreate is only available for Compose-managed containers")
    core.safe_stack(meta["project"])
    output = core.run_compose(meta["project"], ["up", "-d", "--no-deps", "--force-recreate", meta["service"]], timeout=900)
    return {"ok": True, "output": output}


def remove_container(cid: str):
    meta = _container_meta(cid)
    _require_mutable(meta, "remove")
    if meta["composeManaged"]:
        core.safe_stack(meta["project"])
        output = core.run_compose(meta["project"], ["rm", "-s", "-f", meta["service"]], timeout=300)
    else:
        output = engine_cli(["rm", "-f", meta["id"]], timeout=300)
    return {"ok": True, "output": output}


def protected_container_action(cid: str, action: str):
    meta = _container_meta(cid)
    _require_mutable(meta, action)
    return core.container_action(cid, action)


def do_GET_v060(self):
    try:
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/inspect", path)
        if match:
            if not self.require_auth():
                return
            self.send_json(inspect_container(match.group(1)))
            return
    except FileNotFoundError:
        self.send_json({"error": "not found"}, 404)
        return
    except PermissionError as exc:
        self.send_json({"error": str(exc)}, 409)
        return
    except Exception as exc:
        self.send_json({"error": str(exc)}, 500)
        return
    return _original_get(self)


def do_POST_v060(self):
    try:
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/(start|stop|restart|update|recreate|remove)", path)
        if match:
            if not self.require_auth(csrf=True):
                return
            cid, action = match.groups()
            if action in ("start", "stop", "restart"):
                result = protected_container_action(cid, action)
            elif action == "update":
                result = update_container(cid)
            elif action == "recreate":
                result = recreate_container(cid)
            else:
                result = remove_container(cid)
            self.send_json(result)
            return
    except FileNotFoundError:
        self.send_json({"error": "not found"}, 404)
        return
    except PermissionError as exc:
        self.send_json({"error": str(exc)}, 409)
        return
    except Exception as exc:
        self.send_json({"error": str(exc)}, 500)
        return
    return _original_post(self)


core.Handler.do_GET = do_GET_v060
core.Handler.do_POST = do_POST_v060

if __name__ == "__main__":
    core.main()
