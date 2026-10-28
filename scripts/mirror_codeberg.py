#!/usr/bin/env python3
"""Opt-in, non-destructive Codeberg replication; dry-run unless explicitly applied."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


SOURCE_REPOSITORY = "zedarvates/kanboard-neo"
SOURCE_URL = f"https://github.com/{SOURCE_REPOSITORY}.git"
REFSPECS = ("refs/heads/*:refs/heads/*", "refs/tags/*:refs/tags/*")


def fail(message: str) -> None:
    # Never include configuration values, subprocess output or exceptions here.
    print(f"Codeberg mirror: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_git(arguments: list[str], env: dict[str, str], failure: str) -> None:
    try:
        result = subprocess.run(
            ["git", *arguments], env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=180, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        fail(failure)
    if result.returncode:
        fail(failure)


def main() -> int:
    config = os.environ
    if config.get("CODEBERG_MIRROR_ENABLED") != "true":
        print("Codeberg mirror disabled; no network operations performed.")
        return 0

    if (
        config.get("GITHUB_REPOSITORY") != SOURCE_REPOSITORY
        or config.get("GITHUB_REF") != "refs/heads/main"
        or config.get("GITHUB_EVENT_NAME") not in ("push", "workflow_dispatch")
        or config.get("GITHUB_ACTOR") != "zedarvates"
        or config.get("GITHUB_REPOSITORY_OWNER") != "zedarvates"
    ):
        fail("only the repository owner may mirror the canonical source on main.")

    destination = config.get("CODEBERG_MIRROR_REPOSITORY", "")
    if (
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", destination)
        or any(part.endswith(".git") for part in destination.lower().split("/"))
    ):
        fail("set CODEBERG_MIRROR_REPOSITORY to the confirmed owner/repository (without .git).")
    for name in ("CODEBERG_USERNAME", "CODEBERG_TOKEN"):
        value = config.get(name, "")
        if not value.strip() or any(char in value for char in "\r\n\0"):
            fail(f"{name} is missing or invalid; configure it as an Actions secret.")
    apply = config.get("CODEBERG_MIRROR_APPLY", "false")
    if apply not in ("true", "false"):
        fail("CODEBERG_MIRROR_APPLY must be true or false.")

    env = dict(config)
    # Ignore credential helpers, URL rewrites and trace destinations inherited
    # from the runner. Credentials never enter arguments or repository config.
    for name in list(env):
        if name.startswith(("GIT_TRACE", "GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            del env[name]
    env.pop("GIT_CONFIG_COUNT", None)
    env.pop("GIT_CONFIG_PARAMETERS", None)
    env.pop("GIT_CURL_VERBOSE", None)
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_ALLOW_PROTOCOL": "https", "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
    })

    with tempfile.TemporaryDirectory(prefix="codeberg-mirror-") as directory:
        snapshot = str(Path(directory) / "source.git")
        # Bare clone maps every source branch to refs/heads, unlike checkout.
        run_git(["clone", "--bare", "--quiet", SOURCE_URL, snapshot], env,
                "source snapshot failed; nothing was pushed.")
        run_git(["-C", snapshot, "show-ref", "--verify", "--quiet", "refs/heads/main"],
                env, "source main is missing; nothing was pushed.")

        askpass = Path(directory) / "askpass.sh"
        askpass.write_text(
            '#!/bin/sh\ncase "$1" in\n'
            '  *Username*) printf \'%s\\n\' "$CODEBERG_USERNAME" ;;\n'
            '  *Password*) printf \'%s\\n\' "$CODEBERG_TOKEN" ;;\n'
            '  *) exit 1 ;;\nesac\n', encoding="utf-8",
        )
        askpass.chmod(0o700)
        env["GIT_ASKPASS"] = str(askpass)
        command = [
            "-c", "credential.helper=", "-c", "credential.useHttpPath=true",
            "-c", "http.followRedirects=false", "-C", snapshot, "push", "--atomic",
        ]
        target = f"https://codeberg.org/{destination}.git"
        run_git([*command, "--dry-run", target, *REFSPECS], env,
                "dry run rejected (access, divergence or server capability); nothing was pushed.")
        print("Codeberg mirror dry run succeeded; no references changed by the dry run.")
        if apply == "true":
            run_git([*command, target, *REFSPECS], env,
                    "push failed; inspect remote references before retrying.")
            print("Codeberg mirror push succeeded (branches and tags; no force or deletions).")
        else:
            print("Dry-run only. Apply explicitly after reviewing the destination and access.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
