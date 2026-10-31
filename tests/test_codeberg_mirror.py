#!/usr/bin/env python3
"""Exercise mirror guards and real Git semantics using only temporary local repos."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/mirror_codeberg.py"
REAL_GIT = shutil.which("git")
SOURCE_URL = "https://github.com/zedarvates/kanboard-neo.git"
DESTINATION_URL = "https://codeberg.org/mirror-owner/kanboard-neo.git"
USERNAME = "fixture-mirror-user"
TOKEN = "fixture-token-$(never-execute)-sensitive"


@unittest.skipUnless(REAL_GIT, "git is required for local mirror simulations")
class CodebergMirrorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.work = self.directory / "work"
        self.source = self.directory / "source.git"
        self.destination = self.directory / "destination.git"
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        self.log = self.directory / "git-calls.jsonl"
        self.git_env = {
            **os.environ,
            "GIT_ALLOW_PROTOCOL": "file",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Mirror fixture",
            "GIT_AUTHOR_EMAIL": "mirror@example.invalid",
            "GIT_COMMITTER_NAME": "Mirror fixture",
            "GIT_COMMITTER_EMAIL": "mirror@example.invalid",
        }
        self.git("init", "--quiet", "--initial-branch=main", str(self.work))
        (self.work / "file.txt").write_text("initial\n", encoding="utf-8")
        self.git("add", "file.txt", cwd=self.work)
        self.git("commit", "--quiet", "-m", "Initial fixture", cwd=self.work)
        self.git("branch", "feature/retained", cwd=self.work)
        self.git("tag", "v1", cwd=self.work)
        self.git("clone", "--bare", "--quiet", str(self.work), str(self.source))
        self.git("init", "--bare", "--quiet", "--initial-branch=main", str(self.destination))
        self._write_wrapper()
        self.env = {
            **self.git_env,
            "PATH": str(self.bin) + os.pathsep + os.environ.get("PATH", ""),
            "MIRROR_TEST_REAL_GIT": REAL_GIT or "",
            "MIRROR_TEST_SOURCE": str(self.source),
            "MIRROR_TEST_DESTINATION": str(self.destination),
            "MIRROR_TEST_LOG": str(self.log),
            "GITHUB_REPOSITORY": "zedarvates/kanboard-neo",
            "GITHUB_REPOSITORY_OWNER": "zedarvates",
            "GITHUB_ACTOR": "zedarvates",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_EVENT_NAME": "push",
            "CODEBERG_MIRROR_ENABLED": "true",
            "CODEBERG_MIRROR_REPOSITORY": "mirror-owner/kanboard-neo",
            "CODEBERG_MIRROR_APPLY": "false",
            "CODEBERG_USERNAME": USERNAME,
            "CODEBERG_TOKEN": TOKEN,
        }

    def git(self, *args: str, cwd: Path | None = None) -> str:
        result = subprocess.run(
            [REAL_GIT or "git", *args],
            cwd=cwd,
            env=self.git_env,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()

    def refs(self) -> dict[str, str]:
        output = self.git(
            "--git-dir=" + str(self.destination),
            "for-each-ref",
            "--format=%(refname) %(objectname)",
        )
        return dict(line.split(" ", 1) for line in output.splitlines())

    def calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def run_mirror(self, **overrides: str | None) -> subprocess.CompletedProcess[str]:
        environment = dict(self.env)
        for name, value in overrides.items():
            if value is None:
                environment.pop(name, None)
            else:
                environment[name] = value
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
        )

    def _write_wrapper(self) -> None:
        wrapper = self.bin / "git"
        wrapper.write_text(
            "#!" + sys.executable + "\n" + r'''
import json
import os
from pathlib import Path
import subprocess
import sys

args = sys.argv[1:]
source = "https://github.com/zedarvates/kanboard-neo.git"
destination = "https://codeberg.org/mirror-owner/kanboard-neo.git"
entry = {"args": args, "cwd": os.getcwd()}
askpass = os.environ.get("GIT_ASKPASS")
if destination in args:
    entry["terminal_prompt"] = os.environ.get("GIT_TERMINAL_PROMPT")
    if askpass:
        path = Path(askpass)
        entry["askpass"] = str(path)
        entry["askpass_mode"] = path.stat().st_mode & 0o777
        contents = path.read_text()
        entry["askpass_contains_secret"] = any(
            os.environ[name] in contents
            for name in ("CODEBERG_USERNAME", "CODEBERG_TOKEN")
        )
        entry["askpass_works"] = all(
            subprocess.run([askpass, prompt], text=True, capture_output=True, check=True).stdout.rstrip("\n")
            == os.environ[name]
            for prompt, name in (
                ("Username for 'https://codeberg.org': ", "CODEBERG_USERNAME"),
                ("Password for 'https://codeberg.org': ", "CODEBERG_TOKEN"),
            )
        )
with open(os.environ["MIRROR_TEST_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(entry) + "\n")
if destination in args and os.environ.get("MIRROR_TEST_FAIL_DESTINATION"):
    print(os.environ["CODEBERG_TOKEN"], file=sys.stderr)
    sys.exit(72)
rewritten = []
for arg in args:
    if arg == source:
        arg = os.environ["MIRROR_TEST_SOURCE"]
    elif arg == destination:
        arg = os.environ["MIRROR_TEST_DESTINATION"]
    elif "://" in arg:
        print("unexpected network URL rejected by local fixture", file=sys.stderr)
        sys.exit(98)
    rewritten.append(arg)
# Production deliberately allows HTTPS only; after replacing both approved URLs
# with local fixture paths, allow file transport only for the actual Git call.
local_env = dict(os.environ, GIT_ALLOW_PROTOCOL="file")
sys.exit(subprocess.call([os.environ["MIRROR_TEST_REAL_GIT"], *rewritten], env=local_env))
''',
            encoding="utf-8",
        )
        wrapper.chmod(0o700)

    def assert_no_secrets(self, result: subprocess.CompletedProcess[str]) -> None:
        combined = result.stdout + result.stderr
        if self.log.exists():
            combined += self.log.read_text()
        self.assertNotIn(USERNAME, combined)
        self.assertNotIn(TOKEN, combined)

    def test_disabled_does_not_invoke_git(self) -> None:
        for value in (None, "false", "", "TRUE", "yes"):
            with self.subTest(value=value):
                result = self.run_mirror(CODEBERG_MIRROR_ENABLED=value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.calls(), [])

    def test_invalid_preflight_does_not_invoke_git(self) -> None:
        cases = [
            {"GITHUB_REPOSITORY": "someone/kanboard-neo"},
            {"GITHUB_REPOSITORY_OWNER": "someone"},
            {"GITHUB_ACTOR": "someone"},
            {"GITHUB_REF": "refs/heads/unsafe"},
            {"GITHUB_EVENT_NAME": "delete"},
            {"GITHUB_EVENT_NAME": "pull_request"},
            {"CODEBERG_MIRROR_REPOSITORY": None},
            {"CODEBERG_MIRROR_REPOSITORY": ""},
            {"CODEBERG_MIRROR_REPOSITORY": "owner/repo.git"},
            {"CODEBERG_MIRROR_REPOSITORY": "../repo"},
            {"CODEBERG_MIRROR_REPOSITORY": "owner/.."},
            {"CODEBERG_MIRROR_REPOSITORY": "owner/repo/extra"},
            {"CODEBERG_MIRROR_REPOSITORY": "https://codeberg.org/owner/repo"},
            {"CODEBERG_MIRROR_REPOSITORY": "owner/repo\n"},
            {"CODEBERG_MIRROR_APPLY": "yes"},
            {"CODEBERG_MIRROR_APPLY": "TRUE"},
            {"CODEBERG_USERNAME": None},
            {"CODEBERG_TOKEN": None},
            {"CODEBERG_USERNAME": "   "},
            {"CODEBERG_TOKEN": "\t "},
            {"CODEBERG_USERNAME": "unsafe\nuser"},
            {"CODEBERG_TOKEN": "unsafe\rsecret"},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                result = self.run_mirror(**overrides)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.calls(), [])
                self.assert_no_secrets(result)
                for value in overrides.values():
                    if value and "unsafe" in value:
                        self.assertNotIn(value, result.stdout + result.stderr)

    def test_default_dry_run_does_not_modify_destination(self) -> None:
        result = self.run_mirror(CODEBERG_MIRROR_APPLY=None)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.refs(), {})
        pushes = [call for call in self.calls() if "push" in call["args"]]
        self.assertEqual(len(pushes), 1)
        self.assertIn("--dry-run", pushes[0]["args"])
        self.assertIn("--atomic", pushes[0]["args"])
        self.assert_no_secrets(result)

    def test_nul_in_secret_is_rejected_before_git(self) -> None:
        # POSIX itself rejects NULs in subprocess environments. Inject a plain
        # mapping in-process to exercise the script's defensive validation.
        spec = importlib.util.spec_from_file_location("mirror_under_test", SCRIPT)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        with mock.patch.object(sys, "dont_write_bytecode", True):
            spec.loader.exec_module(module)
        environment = {**self.env, "CODEBERG_TOKEN": "invalid\0secret"}
        output = io.StringIO()
        with mock.patch.object(module.os, "environ", environment), \
                mock.patch.object(module, "run_git") as run_git, \
                contextlib.redirect_stderr(output):
            with self.assertRaises(SystemExit) as error:
                module.main()
        self.assertEqual(error.exception.code, 1)
        run_git.assert_not_called()
        self.assertNotIn("invalid\0secret", output.getvalue())

    def test_missing_source_main_prevents_push(self) -> None:
        self.git("--git-dir=" + str(self.source), "symbolic-ref", "HEAD", "refs/heads/feature/retained")
        self.git("--git-dir=" + str(self.source), "branch", "-D", "main")
        result = self.run_mirror(CODEBERG_MIRROR_APPLY="true")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.refs(), {})
        self.assertFalse(any("push" in call["args"] for call in self.calls()))
        self.assert_no_secrets(result)

    def test_apply_copies_all_branches_and_tags_without_deleting_extra_refs(self) -> None:
        self.git("push", "--quiet", str(self.destination), "main:refs/heads/codeberg-only", cwd=self.work)
        self.git("push", "--quiet", str(self.destination), "main:refs/tags/codeberg-only", cwd=self.work)
        before = self.refs()
        result = self.run_mirror(CODEBERG_MIRROR_APPLY="true", GITHUB_EVENT_NAME="workflow_dispatch")
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = {
            "refs/heads/main",
            "refs/heads/feature/retained",
            "refs/tags/v1",
            "refs/heads/codeberg-only",
            "refs/tags/codeberg-only",
        }
        self.assertEqual(set(self.refs()), expected)
        self.assertEqual(self.refs()["refs/heads/codeberg-only"], before["refs/heads/codeberg-only"])
        self.assertEqual(self.refs()["refs/tags/codeberg-only"], before["refs/tags/codeberg-only"])
        for ref in ("refs/heads/main", "refs/heads/feature/retained", "refs/tags/v1"):
            self.assertEqual(self.refs()[ref], self.git("--git-dir=" + str(self.source), "rev-parse", ref))
        pushes = [call for call in self.calls() if "push" in call["args"]]
        self.assertEqual(len(pushes), 2)
        self.assertIn("--dry-run", pushes[0]["args"])
        self.assertNotIn("--dry-run", pushes[1]["args"])
        for call in pushes:
            args = call["args"]
            self.assertIn("--atomic", args)
            self.assertIn("refs/heads/*:refs/heads/*", args)
            self.assertIn("refs/tags/*:refs/tags/*", args)
            self.assertFalse(any(arg in ("--force", "-f", "--prune", "--mirror") or arg.startswith("+") for arg in args))
        self.assert_no_secrets(result)

    def test_divergent_branch_is_rejected_atomically(self) -> None:
        (self.work / "file.txt").write_text("Codeberg advanced independently\n", encoding="utf-8")
        self.git("commit", "--quiet", "-am", "Destination-only commit", cwd=self.work)
        self.git("push", "--quiet", str(self.destination), "main", cwd=self.work)
        before = self.refs()
        result = self.run_mirror(CODEBERG_MIRROR_APPLY="true")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.refs(), before)
        pushes = [call for call in self.calls() if "push" in call["args"]]
        self.assertEqual(len(pushes), 1, "a rejected simulation must prevent apply")
        self.assert_no_secrets(result)

    def test_divergent_tag_is_rejected_atomically(self) -> None:
        (self.work / "file.txt").write_text("different tag target\n", encoding="utf-8")
        self.git("commit", "--quiet", "-am", "Destination-only tag commit", cwd=self.work)
        self.git("tag", "--force", "v1", cwd=self.work)
        self.git("push", "--quiet", str(self.destination), "refs/tags/v1", cwd=self.work)
        before = self.refs()
        result = self.run_mirror(CODEBERG_MIRROR_APPLY="true")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.refs(), before)
        self.assert_no_secrets(result)

    def test_destination_without_atomic_support_prevents_apply(self) -> None:
        self.git(
            "--git-dir=" + str(self.destination),
            "config", "receive.advertiseAtomic", "false",
        )
        result = self.run_mirror(CODEBERG_MIRROR_APPLY="true")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.refs(), {})
        pushes = [call for call in self.calls() if "push" in call["args"]]
        self.assertEqual(len(pushes), 1, "unsupported atomic simulation must prevent apply")
        self.assertIn("--dry-run", pushes[0]["args"])
        self.assertIn("--atomic", pushes[0]["args"])
        self.assert_no_secrets(result)

    def test_apply_hook_rejection_rolls_back_every_reference(self) -> None:
        hook = self.destination / "hooks" / "update"
        hook.write_text(
            '#!/bin/sh\n'
            'printf \'%s\\n\' "$1" >> hooks/update-visited\n'
            'if [ "$1" = refs/heads/main ]; then exit 1; fi\n'
            'exit 0\n',
            encoding="utf-8",
        )
        hook.chmod(0o700)
        hook_trace = self.destination / "hooks" / "update-visited"
        simulation = self.run_mirror()
        self.assertEqual(simulation.returncode, 0, simulation.stderr)
        self.assertFalse(hook_trace.exists(), "dry-run must not execute destination update hooks")
        self.assertEqual(self.refs(), {})
        self.assert_no_secrets(simulation)
        self.log.write_text("", encoding="utf-8")
        result = self.run_mirror(CODEBERG_MIRROR_APPLY="true")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.refs(), {}, "atomic apply must leave no partial branch/tag publication")
        pushes = [call for call in self.calls() if "push" in call["args"]]
        self.assertEqual(len(pushes), 2, "the simulation should succeed before the hook rejects apply")
        self.assertIn("--dry-run", pushes[0]["args"])
        self.assertNotIn("--dry-run", pushes[1]["args"])
        self.assertTrue(all("--atomic" in call["args"] for call in pushes))
        self.assertIn("dry run succeeded", result.stdout)
        self.assertIn("refs/heads/main", hook_trace.read_text().splitlines())
        self.assert_no_secrets(result)

    def test_authentication_is_ephemeral_and_not_embedded_in_urls(self) -> None:
        result = self.run_mirror()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        pushes = [call for call in calls if "push" in call["args"]]
        self.assertEqual(len(pushes), 1)
        push = pushes[0]
        self.assertEqual(push["terminal_prompt"], "0")
        self.assertEqual(push["askpass_mode"], 0o700)
        self.assertFalse(push["askpass_contains_secret"])
        self.assertTrue(push["askpass_works"])
        self.assertIn("credential.helper=", push["args"])
        self.assertIn("credential.useHttpPath=true", push["args"])
        self.assertIn(DESTINATION_URL, push["args"])
        self.assertFalse(Path(push["askpass"]).exists())
        clone = next(call for call in calls if "clone" in call["args"])
        self.assertIn("--bare", clone["args"])
        self.assertIn(SOURCE_URL, clone["args"])
        self.assertFalse(Path(clone["args"][-1]).exists())
        self.assert_no_secrets(result)

    def test_git_failure_does_not_expose_stderr_secret_and_cleans_up(self) -> None:
        result = self.run_mirror(MIRROR_TEST_FAIL_DESTINATION="1", CODEBERG_MIRROR_APPLY="true")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.refs(), {})
        self.assert_no_secrets(result)
        calls = self.calls()
        push = next(call for call in calls if "push" in call["args"])
        self.assertFalse(Path(push["askpass"]).exists())
        clone = next(call for call in calls if "clone" in call["args"])
        self.assertFalse(Path(clone["args"][-1]).exists())


if __name__ == "__main__":
    unittest.main()
