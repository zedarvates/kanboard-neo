# Kanboard Neo — current status

Last reviewed: 2026-08-09

## Verified repository facts

- Public fork based on Kanboard, with a Linear-inspired theme and workflow.
- Runtime requires PHP 8.1+ and Composer.
- Pull requests run SQLite and PostgreSQL PHPUnit suites plus JavaScript and PHP
  linters.
- JSON-RPC exposes project and task read/write procedures behind authentication
  and role/project authorization for authenticated users.
- The special application credential named `jsonrpc` is not a least-privilege
  cockpit credential: user and project authorization checks are conditional on a
  logged user session.

## Functional state

### Verified or covered by existing code

- Standard Kanboard project/task models and JSON-RPC procedures.
- SQLite/PostgreSQL CI definitions.
- Linear-style theme, command palette, workflow columns, dashboard cards and
  activity-feed templates.

### Under repair

- Dashboard dynamic statistics introduced by commit `da43a2a4` have a dedicated
  fix in PR #10 and issue #9. Until that PR passes and is merged, the dashboard
  may fail before rendering.

### Prepared but not activated

- Private portfolio registry in Botte Secrète PR #54.
- Read-only registry validator/diff in Botte Secrète PR #58.
- Kanboard portfolio integration contract in `docs/PORTFOLIO_INTEGRATION.md`.

### Explicitly absent

- No live connection from Botte Secrète to Kanboard Neo.
- No automatic project or task creation.
- No Hostinger or production deployment integration.
- No Memory Hub import.
- No credential provisioning or secrets management implementation.

## Next safe gate

After PR #10 and the Botte registry/read-only validator are reviewed, generate a
sanitized portfolio preview outside Kanboard. Import nothing until the preview,
field mapping, confidentiality projection, and idempotency rules have been
reviewed by the owner.
