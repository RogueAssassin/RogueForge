#!/usr/bin/env python3
"""RogueForge v0.7.1 runtime.

Combines the 0.7 live operations layer with flexible Compose discovery.
"""
from __future__ import annotations

from urllib.parse import urlparse

import rogueforge as core
import rogueforge_live  # installs live-log/terminal handlers
import rogueforge_discovery as discovery  # installs flexible stack resolution

VERSION = "0.7.1"
core.VERSION = VERSION
core.Handler.server_version = f"RogueForge/{VERSION}"
_previous_get = core.Handler.do_GET
_discover_stacks = core.discover_stacks


def public_stack_list():
    """Expose useful discovery metadata without leaking absolute host paths."""
    result = []
    for stack in _discover_stacks():
        item = dict(stack)
        item.pop("directory", None)
        item.pop("composePath", None)
        result.append(item)
    return result


core.discover_stacks = public_stack_list


def do_GET_v071(self):
    if urlparse(self.path).path == "/api/discovery":
        if not self.require_auth():
            return
        try:
            self.send_json(discovery.discovery_diagnostics())
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)
        return
    return _previous_get(self)


core.Handler.do_GET = do_GET_v071

if __name__ == "__main__":
    core.main()
