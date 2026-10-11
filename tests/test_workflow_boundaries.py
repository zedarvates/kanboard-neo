#!/usr/bin/env python3
"""Deterministic positive and negative probes for publishing owner gates."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_workflow_boundaries import (  # noqa: E402
    OWNER_GATES,
    workflow_boundary_errors,
)


class WorkflowBoundaryTests(unittest.TestCase):
    def test_owner_gates_are_present(self) -> None:
        self.assertEqual(workflow_boundary_errors(ROOT), [])

    def test_missing_owner_gate_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = Path(directory)
            for relative in OWNER_GATES:
                destination = fixture_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)

            mirror = fixture_root / ".github/workflows/codeberg_mirror.yml"
            mirror.write_text(
                mirror.read_text(encoding="utf-8").replace(
                    "    if: ${{ github.actor == github.repository_owner }}\n",
                    "",
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                workflow_boundary_errors(fixture_root),
                [
                    "missing repository-owner gate: "
                    ".github/workflows/codeberg_mirror.yml"
                ],
            )


if __name__ == "__main__":
    unittest.main()
