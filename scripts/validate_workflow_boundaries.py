#!/usr/bin/env python3
"""Fail closed when publishing workflows lose their repository-owner gates."""

from __future__ import annotations

import sys
from pathlib import Path


OWNER_GATES = {
    ".github/workflows/codeberg_mirror.yml": (
        "  mirror:\n"
        "    if: ${{ github.actor == github.repository_owner }}\n"
    ),
    ".github/workflows/docker.yml": (
        "  multiplatform-build:\n"
        "    if: ${{ github.event_name != 'pull_request' && "
        "github.actor == github.repository_owner }}\n"
    ),
}


def workflow_boundary_errors(root: str | Path = ".") -> list[str]:
    project = Path(root)
    errors: list[str] = []
    for relative, owner_gate in OWNER_GATES.items():
        path = project / relative
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            errors.append(f"missing workflow: {relative}")
            continue
        if owner_gate not in content:
            errors.append(f"missing repository-owner gate: {relative}")
    return errors


def main() -> int:
    errors = workflow_boundary_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("workflow boundaries: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
