#!/usr/bin/env python3
"""Run the current cross-repo local validation batch without installing anything.

Targets:
- StoryCore PR #42 semantic pre-validator
- StoryCore PR #43 multi-subject router
- Ultimate Odycer tools PR #13 Godot validation contracts
- Ultimate Odycer tools PR #14 XR evidence contracts

The runner only reads repositories and executes targeted test commands. It does not
fetch, checkout, install dependencies, mutate source files, reboot, or access the
network intentionally. Results are written to a JSON report outside tested repos by
default.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class Target:
    name: str
    repo_env: str
    repo_candidates: tuple[str, ...]
    required_ref_hint: str
    command: tuple[str, ...]


TARGETS = (
    Target(
        name="storycore-semantic-prevalidator",
        repo_env="STORYCORE_REPO",
        repo_candidates=("StoryCore-Engine", "storycore-engine"),
        required_ref_hint="codex/semantic-video-prevalidator (PR #42)",
        command=(sys.executable, "-m", "pytest", "-q", "tests/test_semantic_prevalidator.py"),
    ),
    Target(
        name="storycore-multisubject-router",
        repo_env="STORYCORE_REPO",
        repo_candidates=("StoryCore-Engine", "storycore-engine"),
        required_ref_hint="codex/multi-subject-video-router (PR #43)",
        command=(
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_multi_subject_router.py",
            "tests/test_shot_spec_router_adapter.py",
        ),
    ),
    Target(
        name="godot-validation-foundation",
        repo_env="ULTOD_TOOLS_REPO",
        repo_candidates=("ultimate-odycer-tools-suite",),
        required_ref_hint="codex/godot-validation-foundation (PR #13)",
        command=("node", "--test", "ops/godot-validation/test.mjs"),
    ),
    Target(
        name="xr-operator-evidence-contract",
        repo_env="ULTOD_TOOLS_REPO",
        repo_candidates=("ultimate-odycer-tools-suite",),
        required_ref_hint="codex/xr-operator-fixture-contract (PR #14)",
        command=("node", "--test", "ops/xr-operator-validation/test.mjs"),
    ),
)


def _redact(text: str, roots: Sequence[Path]) -> str:
    value = text or ""
    replacements = [(Path.home(), "<home>")]
    replacements.extend((root, f"<repo:{root.name}>") for root in roots)
    for path, marker in replacements:
        try:
            raw = str(path.resolve())
        except OSError:
            raw = str(path)
        for variant in {raw, raw.replace("\\", "/"), raw.replace("/", "\\")}:
            value = value.replace(variant, marker)
    return value


def _run(command: Sequence[str], cwd: Path, roots: Sequence[Path], timeout: int) -> dict:
    started = time.monotonic()
    executable = shutil.which(command[0]) if not Path(command[0]).is_file() else command[0]
    if executable is None:
        return {
            "status": "BLOCKED",
            "reason": f"executable_not_found:{command[0]}",
            "command": list(command),
            "duration_s": 0.0,
            "returncode": None,
            "stdout": "",
            "stderr": "",
        }
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "FAIL",
            "reason": "timeout",
            "command": list(command),
            "duration_s": round(time.monotonic() - started, 3),
            "returncode": 124,
            "stdout": _redact(exc.stdout if isinstance(exc.stdout, str) else "", roots)[-6000:],
            "stderr": _redact(exc.stderr if isinstance(exc.stderr, str) else "", roots)[-6000:],
        }

    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "reason": None,
        "command": list(command),
        "duration_s": round(time.monotonic() - started, 3),
        "returncode": completed.returncode,
        "stdout": _redact(completed.stdout, roots)[-6000:],
        "stderr": _redact(completed.stderr, roots)[-6000:],
    }


def _git_head(repo: Path) -> dict:
    git = shutil.which("git")
    if not git or not (repo / ".git").exists():
        return {"branch": None, "sha": None, "dirty": None}

    def one(*args: str) -> str | None:
        proc = subprocess.run([git, *args], cwd=repo, capture_output=True, text=True, check=False)
        return proc.stdout.strip() if proc.returncode == 0 else None

    branch = one("branch", "--show-current")
    sha = one("rev-parse", "HEAD")
    status = one("status", "--porcelain")
    return {"branch": branch, "sha": sha, "dirty": bool(status) if status is not None else None}


def _find_repo(target: Target, roots: Sequence[Path]) -> Path | None:
    explicit = os.getenv(target.repo_env)
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.is_dir():
            return candidate.resolve()

    for root in roots:
        for name in target.repo_candidates:
            candidate = root / name
            if candidate.is_dir():
                return candidate.resolve()
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        action="append",
        type=Path,
        default=[],
        help="parent directory containing cloned repos; may be repeated",
    )
    parser.add_argument("--report", type=Path, default=Path.cwd() / "local-validation-2026-08-30.json")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)

    roots = [path.expanduser().resolve() for path in args.root]
    if not roots:
        roots = [Path.cwd().resolve(), Path.cwd().resolve().parent]

    repo_cache: dict[str, Path | None] = {}
    results: list[dict] = []

    for target in TARGETS:
        cache_key = target.repo_env
        if cache_key not in repo_cache:
            repo_cache[cache_key] = _find_repo(target, roots)
        repo = repo_cache[cache_key]
        if repo is None:
            results.append({
                "name": target.name,
                "status": "BLOCKED",
                "reason": f"repo_not_found:set_{target.repo_env}",
                "required_ref_hint": target.required_ref_hint,
                "repo": None,
                "git": None,
                "run": None,
            })
            continue

        run = _run(target.command, repo, [r for r in repo_cache.values() if r], args.timeout)
        results.append({
            "name": target.name,
            "status": run["status"],
            "reason": run.get("reason"),
            "required_ref_hint": target.required_ref_hint,
            "repo": repo.name,
            "git": _git_head(repo),
            "run": run,
        })

    statuses = [item["status"] for item in results]
    overall = "PASS" if statuses and all(status == "PASS" for status in statuses) else (
        "FAIL" if any(status == "FAIL" for status in statuses) else "BLOCKED"
    )
    payload = {
        "schema": "kanboard-local-validation-batch/v1",
        "date": "2026-08-30",
        "overall": overall,
        "network_install_performed": False,
        "reboot_performed": False,
        "source_mutation_intended": False,
        "results": results,
    }

    report = args.report.expanduser().resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps({"overall": overall, "report": report.name}, sort_keys=True))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
