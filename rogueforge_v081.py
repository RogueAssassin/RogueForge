#!/usr/bin/env python3
"""RogueForge v0.8.1 UI/icon integration release."""
import rogueforge as core
import rogueforge_v080  # installs v0.8 stack-first handlers

VERSION = "0.8.1"
core.VERSION = VERSION
core.Handler.server_version = f"RogueForge/{VERSION}"

if __name__ == "__main__":
    core.main()
