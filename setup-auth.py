#!/usr/bin/env python3
"""Provision the local RogueForge administrator without storing a plaintext password."""
import argparse
import base64
import getpass
import hashlib
import json
import os
from pathlib import Path
import secrets
import string
import sys

ITERATIONS = 600_000


def encoded(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def generated_password(length=24):
    alphabet = string.ascii_letters + string.digits + "-_.!@"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main():
    parser = argparse.ArgumentParser(description="Create or replace the RogueForge administrator account")
    parser.add_argument("--username", default="administrator")
    parser.add_argument("--auth-file", default="data/auth.json")
    parser.add_argument("--generate", action="store_true", help="generate and display a strong password once")
    args = parser.parse_args()

    if not args.username or len(args.username) > 64 or not all(char.isalnum() or char in "._-" for char in args.username):
        parser.error("username may contain only letters, numbers, dot, underscore, and hyphen")

    if args.generate:
        password = generated_password()
        confirmation = password
    else:
        password = getpass.getpass("New RogueForge password: ")
        confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 1
    if len(password) < 12:
        print("Password must contain at least 12 characters.", file=sys.stderr)
        return 1

    salt = secrets.token_bytes(24)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    record = {
        "version": 1,
        "username": args.username,
        "algorithm": "pbkdf2-sha256",
        "iterations": ITERATIONS,
        "salt": encoded(salt),
        "passwordHash": encoded(digest),
        "sessionSecret": encoded(secrets.token_bytes(48)),
    }
    destination = Path(args.auth_file).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, destination)
    print(f"Administrator '{args.username}' configured in {destination}")
    if args.generate:
        print(f"Generated password (shown once): {password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
