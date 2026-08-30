from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_local_validation_batch.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("local_validation_batch", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_redact_removes_repo_and_home_paths(tmp_path):
    module = _load_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    text = f"error in {repo}/file.py and {Path.home()}/secret"
    redacted = module._redact(text, [repo])
    assert str(repo) not in redacted
    assert str(Path.home()) not in redacted
    assert "<repo:repo>" in redacted


def test_run_reports_blocked_when_executable_missing(tmp_path):
    module = _load_module()
    result = module._run(
        ["definitely-not-a-real-executable-ultod", "--version"],
        cwd=tmp_path,
        roots=[tmp_path],
        timeout=1,
    )
    assert result["status"] == "BLOCKED"
    assert result["returncode"] is None


def test_find_repo_prefers_explicit_environment(tmp_path, monkeypatch):
    module = _load_module()
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    monkeypatch.setenv("STORYCORE_REPO", str(explicit))
    target = module.TARGETS[0]
    assert module._find_repo(target, [tmp_path / "other"]) == explicit.resolve()


def test_git_head_is_read_only_for_non_git_directory(tmp_path):
    module = _load_module()
    before = set(tmp_path.iterdir())
    result = module._git_head(tmp_path)
    after = set(tmp_path.iterdir())
    assert result == {"branch": None, "sha": None, "dirty": None}
    assert before == after
