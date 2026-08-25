#!/usr/bin/env python3
"""RogueForge flexible Compose discovery for v0.7.1.

Resolves Compose projects from runtime labels first, then recursively scans the
configured stack root. This removes the old assumption that every project must
live at STACKS_DIR/<compose-project-name> with a fixed compose filename.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

import rogueforge as core
import rogueforge_ext as ext

SCAN_DEPTH = max(1, min(12, int(os.environ.get("ROGUEFORGE_SCAN_DEPTH", "4"))))
CACHE_SECONDS = max(2, min(300, int(os.environ.get("ROGUEFORGE_DISCOVERY_CACHE", "10"))))
EXCLUDED_DIRS = {".git", ".cache", "node_modules", "__pycache__", "backup", "backups"}
_original_safe_stack = core.safe_stack
_original_compose_file = core.compose_file
_original_meta = ext._container_meta
_cache = {"time": 0.0, "records": [], "aliases": {}, "by_dir": {}}


def _inside_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(core.STACKS_DIR)
        return True
    except ValueError:
        return False


def _normalise_key(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "--", value.strip().strip("/"))
    return value[:127] or "stack"


def _label_values(labels: dict, *keys: str):
    for key in keys:
        value = labels.get(key)
        if value:
            yield str(value)


def _compose_from_labels(labels: dict):
    candidates = []
    for raw in _label_values(
        labels,
        "com.docker.compose.project.config_files",
        "io.podman.compose.project.config_files",
        "com.docker.compose.project.config_file",
        "io.podman.compose.project.config_file",
    ):
        for item in raw.split(","):
            item = item.strip()
            if item:
                candidates.append(Path(item))
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            continue
        if resolved.is_file() and _inside_root(resolved):
            return resolved
    return None


def _working_dir_from_labels(labels: dict):
    for raw in _label_values(
        labels,
        "com.docker.compose.project.working_dir",
        "io.podman.compose.project.working_dir",
        "com.docker.compose.project.working-directory",
    ):
        try:
            path = Path(raw).resolve()
        except Exception:
            continue
        if path.is_dir() and _inside_root(path):
            return path
    return None


def _record(records: dict, directory: Path, compose: Path, project: str | None = None, source="scan"):
    directory = directory.resolve(); compose = compose.resolve()
    if not _inside_root(directory) or not compose.is_file():
        return
    key = str(directory)
    current = records.get(key)
    if current:
        if project and not current.get("project"):
            current["project"] = project
        if source == "labels":
            current["source"] = "labels"
        return
    rel = directory.relative_to(core.STACKS_DIR)
    generated = _normalise_key(str(rel) if str(rel) != "." else directory.name)
    records[key] = {"key": generated, "directory": directory, "compose": compose, "project": project or None, "source": source, "relativePath": str(rel)}


def _scan_recursive(records: dict):
    root = core.STACKS_DIR
    if not root.is_dir():
        return
    for current, dirs, files in os.walk(root):
        path = Path(current)
        try:
            depth = len(path.relative_to(root).parts)
        except ValueError:
            continue
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in EXCLUDED_DIRS]
        if depth >= SCAN_DEPTH:
            dirs[:] = []
        names = set(files)
        for compose_name in core.COMPOSE_NAMES:
            if compose_name in names:
                _record(records, path, path / compose_name, source="scan")
                break


def _runtime_records(records: dict):
    for item in core.load_containers() or []:
        labels = item.get("Labels") or item.get("labels") or {}
        if not isinstance(labels, dict):
            continue
        project = labels.get("com.docker.compose.project") or labels.get("io.podman.compose.project")
        compose = _compose_from_labels(labels)
        working = _working_dir_from_labels(labels)
        if compose:
            _record(records, compose.parent, compose, str(project) if project else None, "labels")
        elif working:
            cf = _original_compose_file(working)
            if cf:
                _record(records, working, cf, str(project) if project else None, "labels")


def _build_registry(force=False):
    now = time.time()
    if not force and now - _cache["time"] < CACHE_SECONDS:
        return _cache
    records = {}
    try:
        _runtime_records(records)
    except Exception:
        pass
    _scan_recursive(records)
    items = list(records.values())
    # Prefer actual Compose project names as keys. Resolve collisions with path-derived keys.
    used = set()
    for rec in items:
        preferred = _normalise_key(rec.get("project") or rec["key"])
        key = preferred
        if key in used:
            key = _normalise_key(f"{preferred}--{rec['relativePath']}")
        suffix = 2
        base = key
        while key in used:
            key = f"{base}-{suffix}"[:127]; suffix += 1
        rec["key"] = key; used.add(key)
    aliases = {}
    by_dir = {}
    for rec in items:
        by_dir[str(rec["directory"])] = rec
        for alias in (rec["key"], rec.get("project"), rec["directory"].name, rec["relativePath"]):
            if alias:
                aliases.setdefault(str(alias), rec)
    _cache.update({"time": now, "records": items, "aliases": aliases, "by_dir": by_dir})
    return _cache


def resolve_stack(value: str):
    registry = _build_registry()
    raw = str(value)
    rec = registry["aliases"].get(raw)
    if rec:
        return rec
    normal = _normalise_key(raw)
    rec = registry["aliases"].get(normal)
    if rec:
        return rec
    raise FileNotFoundError(raw)


def safe_stack(value: str, allow_self=False) -> Path:
    rec = resolve_stack(value)
    identities = {rec["key"], rec.get("project"), rec["directory"].name}
    if core.SELF_STACK in identities and not allow_self:
        raise PermissionError("RogueForge cannot manage its own Compose project from inside itself")
    return rec["directory"]


def compose_file(directory: Path):
    rec = _build_registry()["by_dir"].get(str(directory.resolve()))
    if rec and rec["compose"].is_file():
        return rec["compose"]
    return _original_compose_file(directory)


def container_meta(cid: str):
    meta = _original_meta(cid)
    labels = meta.get("labels") or {}
    project = meta.get("project")
    try:
        rec = None
        if project and project != "standalone":
            rec = _build_registry()["aliases"].get(str(project))
        if not rec:
            compose = _compose_from_labels(labels)
            working = _working_dir_from_labels(labels)
            if compose:
                rec = _build_registry()["by_dir"].get(str(compose.parent.resolve()))
            elif working:
                rec = _build_registry()["by_dir"].get(str(working.resolve()))
        if rec:
            meta["project"] = rec["key"]
            meta["projectDisplay"] = rec.get("project") or rec["directory"].name
            meta["composePath"] = str(rec["compose"])
            meta["composeManaged"] = bool(meta.get("service"))
            meta["discoverySource"] = rec["source"]
    except Exception:
        pass
    return meta


def discover_stacks():
    registry = _build_registry(force=True)
    members = {}
    for item in core.containers():
        try:
            meta = container_meta(item["id"])
            members.setdefault(meta.get("project", "standalone"), []).append(item)
        except Exception:
            pass
    result = []
    for rec in sorted(registry["records"], key=lambda r: r["key"].lower()):
        group = members.get(rec["key"], [])
        running = sum(item.get("state") == "running" for item in group)
        identities = {rec["key"], rec.get("project"), rec["directory"].name}
        result.append({
            "name": rec["key"],
            "displayName": rec.get("project") or rec["directory"].name,
            "composeFile": rec["compose"].name,
            "composePath": str(rec["compose"]),
            "directory": str(rec["directory"]),
            "relativePath": rec["relativePath"],
            "discoverySource": rec["source"],
            "hasEnv": (rec["directory"] / ".env").is_file(),
            "engineHint": "podman" if "podman" in rec["compose"].name else ("docker" if "docker" in rec["compose"].name else "portable"),
            "services": len(group),
            "running": running,
            "state": "running" if group and running == len(group) else ("partial" if running else "stopped"),
            "managed": core.SELF_STACK not in identities,
        })
    return result


def discovery_diagnostics():
    registry = _build_registry(force=True)
    return {
        "scanDepth": SCAN_DEPTH,
        "cacheSeconds": CACHE_SECONDS,
        "stacksRoot": str(core.STACKS_DIR),
        "discovered": len(registry["records"]),
        "stacks": [{"key": r["key"], "project": r.get("project"), "directory": str(r["directory"]), "compose": str(r["compose"]), "source": r["source"]} for r in registry["records"]],
    }


core.safe_stack = safe_stack
core.compose_file = compose_file
core.discover_stacks = discover_stacks
ext._container_meta = container_meta
