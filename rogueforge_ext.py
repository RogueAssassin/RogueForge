#!/usr/bin/env python3
"""RogueForge v0.6.2 container-management extension."""
from __future__ import annotations

import json
import re
from urllib.parse import urlparse

import rogueforge as core

VERSION = "0.6.2"
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


def containers_v062():
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


core.containers = containers_v062


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
    return _remote_podman(args, timeout) if core.runtime()["engine"] == "podman" else _docker_cli(args, timeout)


def inspect_container(cid: str):
    meta = _container_meta(cid)
    raw = engine_cli(["inspect", meta["id"]], timeout=60)
    data = json.loads(raw or "[]")
    inspect = data[0] if isinstance(data, list) and data else data
    state = inspect.get("State") or {}
    config = inspect.get("Config") or {}
    host_config = inspect.get("HostConfig") or {}
    network = inspect.get("NetworkSettings") or {}
    mounts = inspect.get("Mounts") or []
    restart_policy = host_config.get("RestartPolicy") or {}
    if isinstance(restart_policy, str):
        restart_policy = {"Name": restart_policy}
    return {
        **{k: meta[k] for k in ("id", "shortId", "name", "image", "project", "service", "composeManaged", "selfProtected")},
        "created": inspect.get("Created"),
        "status": state.get("Status"),
        "running": state.get("Running"),
        "startedAt": state.get("StartedAt"),
        "finishedAt": state.get("FinishedAt"),
        "restartCount": inspect.get("RestartCount", 0),
        "restartPolicy": restart_policy.get("Name") or restart_policy.get("name") or "none",
        "imageId": inspect.get("Image"),
        "command": config.get("Cmd") or [],
        "entrypoint": config.get("Entrypoint") or [],
        "environment": config.get("Env") or [],
        "mounts": [{"source": m.get("Source"), "destination": m.get("Destination"), "type": m.get("Type"), "rw": m.get("RW")} for m in mounts],
        "networks": list((network.get("Networks") or {}).keys()),
    }


def container_stats():
    try:
        raw = engine_cli(["stats", "--no-stream", "--format", "json"], timeout=60)
        rows = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        if len(rows) == 1 and isinstance(rows[0], list):
            rows = rows[0]
        result = {}
        for row in rows:
            cid = str(row.get("id") or row.get("ID") or row.get("Container") or "")
            name = str(row.get("name") or row.get("Name") or "")
            result[cid[:12] or name] = {
                "cpu": row.get("cpu_percent") or row.get("CPUPerc") or row.get("CPU"),
                "memory": row.get("mem_usage") or row.get("MemUsage"),
                "memoryPercent": row.get("mem_percent") or row.get("MemPerc"),
                "network": row.get("net_io") or row.get("NetIO"),
                "block": row.get("block_io") or row.get("BlockIO"),
                "pids": row.get("pids") or row.get("PIDs"),
            }
        return result
    except Exception:
        return {}


def image_status(cid: str, pull=False):
    meta = _container_meta(cid)
    before = inspect_container(cid).get("imageId")
    output = ""
    if pull:
        output = engine_cli(["pull", meta["image"]], timeout=900)
    try:
        raw = engine_cli(["image", "inspect", meta["image"]], timeout=60)
        data = json.loads(raw or "[]")
        img = data[0] if isinstance(data, list) and data else data
        current = img.get("Id") or img.get("ID")
    except Exception:
        current = None
    return {
        "id": meta["id"],
        "name": meta["name"],
        "image": meta["image"],
        "containerImageId": before,
        "localImageId": current,
        "updateAvailable": bool(before and current and before != current),
        "checkedByPull": pull,
        "output": output[-100_000:],
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
    return {"ok": True, "output": core.run_compose(meta["project"], ["up", "-d", "--no-deps", "--force-recreate", meta["service"]], timeout=900)}


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


def run_container_action(cid: str, action: str):
    if action in ("start", "stop", "restart"):
        return protected_container_action(cid, action)
    if action == "update":
        return update_container(cid)
    if action == "recreate":
        return recreate_container(cid)
    if action == "remove":
        return remove_container(cid)
    if action == "check-update":
        return image_status(cid, pull=True)
    raise ValueError("unsupported action")


def bulk_container_action(ids, action):
    if action not in ("start", "stop", "restart", "update", "recreate", "remove"):
        raise ValueError("unsupported bulk action")
    if not isinstance(ids, list) or not ids or len(ids) > 100:
        raise ValueError("select between 1 and 100 containers")
    results = []
    for cid in ids:
        try:
            if not isinstance(cid, str) or not re.fullmatch(r"[0-9a-fA-F]{12,64}", cid):
                raise ValueError("invalid container id")
            meta = _container_meta(cid)
            result = run_container_action(cid, action)
            results.append({"id": cid, "name": meta["name"], "ok": True, "message": result.get("message"), "output": result.get("output", "")[-4000:]})
        except Exception as exc:
            results.append({"id": str(cid), "ok": False, "error": str(exc)})
    return {"ok": all(item["ok"] for item in results), "action": action, "results": results}


def update_all():
    ids = [item["id"] for item in containers_v062() if not item.get("selfProtected")]
    return bulk_container_action(ids, "update") if ids else {"ok": True, "action": "update", "results": []}


def do_GET_v062(self):
    try:
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/(inspect|image-status)", path)
        if match:
            if not self.require_auth():
                return
            cid, action = match.groups()
            self.send_json(inspect_container(cid) if action == "inspect" else image_status(cid))
            return
        if path == "/api/containers/stats":
            if not self.require_auth():
                return
            self.send_json(container_stats())
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


def do_POST_v062(self):
    try:
        path = urlparse(self.path).path
        if path == "/api/containers/update-all":
            if not self.require_auth(csrf=True):
                return
            self.send_json(update_all())
            return
        if path == "/api/containers/bulk":
            if not self.require_auth(csrf=True):
                return
            payload = self.read_json()
            self.send_json(bulk_container_action(payload.get("ids"), str(payload.get("action") or "")))
            return
        match = re.fullmatch(r"/api/containers/([0-9a-fA-F]+)/(start|stop|restart|update|recreate|remove|check-update)", path)
        if match:
            if not self.require_auth(csrf=True):
                return
            cid, action = match.groups()
            self.send_json(run_container_action(cid, action))
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


core.Handler.do_GET = do_GET_v062
core.Handler.do_POST = do_POST_v062

if __name__ == "__main__":
    core.main()
