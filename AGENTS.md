# AGENTS.md — Kanboard Neo

Guidance for AI coding agents working in this repository.

## Mission

Maintain the Kanboard-based project cockpit without weakening upstream security,
permissions, validation, accessibility, database portability, or tests. Keep
portfolio integrations reversible and read-only until a separate write phase is
explicitly approved.

## Runtime and setup

- PHP: **8.1 or newer**.
- Install dependencies: `composer install --prefer-dist --no-progress --no-suggest`.
- Validate dependency metadata: `composer validate`.
- Default development database: SQLite via `tests/units.sqlite.xml`.

## Required checks

- Focused test: `./vendor/bin/phpunit -c tests/units.sqlite.xml --filter <TestName>`.
- Full SQLite suite: `make test-sqlite`.
- PostgreSQL suite when database code changes: `make test-postgres`.
- JavaScript: `jshint ./assets/js/core ./assets/js/components`.
- PHP style: `php-cs-fixer check --diff --verbose --show-progress none`.
- Commit messages must satisfy `.github/workflows/scripts/commit-checker.py`.

## Change rules

- Never work directly on `main`; use a focused branch and pull request.
- Prefer the smallest change that fixes the verified problem.
- Add a regression test for every bug fix when feasible.
- Preserve SQLite and PostgreSQL behavior; do not introduce driver-specific SQL
  without tests for all supported paths.
- Do not bypass `ProjectAuthorization`, `TaskAuthorization`, `UserAuthorization`,
  validators, CSRF protection, or role checks.
- Do not expose raw HTML from untrusted event, task, project, or portfolio data.
- Do not claim the dashboard, API, or synchronization works without executable
  evidence.

## Portfolio cockpit boundaries

- The private Botte registry is an **index**, not a replacement for project
  repositories or local sources of truth.
- Initial integration is read-only and consumes only a reviewed, sanitized
  projection. It must not read arbitrary local paths from Kanboard.
- Never store API tokens, passwords, SSH keys, absolute personal paths, player or
  customer data, unpublished research, or proprietary Ultimate Odycer internals.
- Do not use the application-wide `jsonrpc` credential for the cockpit. A later
  API integration must use a dedicated least-privilege user and an explicit
  procedure allowlist.
- Creating, updating, moving, closing, or deleting projects/tasks requires a
  separate write phase, dry-run output, idempotency keys, audit logs, and owner
  confirmation.

## Machine-local files

Copy the tracked examples to local ignored files when needed:

```text
.mcp.example.json             -> .mcp.json
.botte/config.example.json    -> .botte/config.json
.claude/settings.example.json -> .claude/settings.json
```

Never commit generated setup reports or machine-specific paths.

## Botte Secrète policy

Read `.botte/policy.md`. Use local models only when the local MCP is actually
configured; absence of `.mcp.json` must not block normal PHP development.
