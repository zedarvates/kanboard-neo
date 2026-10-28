# Codeberg mirror

This workflow is optional and disabled until the repository owner explicitly
configures it. It does not affect the dashboard fix merged in PR #10, application
tests, container publication, the Odin executor or Ultimate Odycer work.

## Incident and destination

The [27 October 2026 run](https://github.com/zedarvates/kanboard-neo/actions/runs/40588638319)
failed at authentication after merging PR #10 on
`8da357420730f4d11847638049b0fc04a39154a5`. The reported log had empty
`CODEBERG_USERNAME` and `CODEBERG_TOKEN`. This does not establish their current
presence or validity in Actions settings.

The old destination, `https://codeberg.org/kanboard/kanboard.git`, was inherited
from commit `e5bc94f9af6513075609806d91a02ba7068d839f`. On 28 October 2026,
the public Codeberg repository API identified its owner as `kanboard`, website
as `https://kanboard.org`, and original URL as
`https://github.com/kanboard/kanboard.git`. These are upstream Kanboard details,
not evidence of ownership or approval for Kanboard Neo replication. No intended
Kanboard Neo destination was found in this repository. There is no default URL
in the corrected workflow: do not copy the inherited destination without
confirming control and intent.

## Replication policy

- Only the repository owner may run the job. Both workflow and script restrict
  the source to `zedarvates/kanboard-neo` on `main`.
- A push to `main` requests an update once enabled. A manual run defaults to a
  dry run; its `apply` checkbox explicitly requests an update.
- Secondary branch changes and tag-only pushes wait for the next `main` push
  or manual run. The `delete` trigger is removed because deletion is no longer
  propagated. This is additive replication, not an exact destructive mirror.
- A fresh bare source clone supplies **all branches and tags**. A normal
  checkout puts other branches in `refs/remotes/origin/*`; pushing only its
  `refs/heads/*` with `--prune` could delete valid destination branches.
- There is no `--force`, `--prune`, `--mirror`, deletion refspec or forced push
  refspec. Extra destination refs remain. Branch rewrites and moved tags are
  rejected. Divergence requires separate owner review, not an automatic force.
- Every update first performs `git push --dry-run --atomic`. Actual updates
  also use `--atomic`: if any ref is rejected, the batch is rejected. A server
  without atomic-push support fails closed. A dry run checks connectivity and
  the proposed ref updates, but cannot prove that all receive hooks or write
  permissions will accept a real push.
- One workflow-specific concurrency group serializes runs. It does not cancel
  an active push or acquire resources belonging to other projects.
- GitHub permissions are `contents: read`; checkout credentials are not saved.
  Codeberg credentials are supplied through a temporary `GIT_ASKPASS` helper,
  never placed in a URL, command argument or Git config. Git output is captured
  and errors are reported without its potentially sensitive contents. Temporary
  repositories and the helper are removed when the script exits normally or
  raises a handled error; the hosted runner handles cancellation cleanup.

## Configuration remaining before activation

1. Confirm the exact Codeberg `owner/repository`, that it is intended to receive
   Kanboard Neo, and that the account has permission to update it. Review any
   existing branches/tags there, especially divergent history. Do not assume
   the GitHub and Codeberg account names match.
2. In GitHub **Settings → Secrets and variables → Actions**, set repository
   variable `CODEBERG_MIRROR_REPOSITORY` to that exact `owner/repository`, with
   no URL, credentials or `.git` suffix. Set secrets `CODEBERG_USERNAME` and
   `CODEBERG_TOKEN` for the authorized Codeberg account, using the narrowest
   available access to that destination. Never paste secret values into a PR,
   issue or log.
3. After the isolated fix has been reviewed and merged, set repository variable
   `CODEBERG_MIRROR_ENABLED` to the literal `true` only when those checks are
   complete. Absent or any other value keeps the workflow inactive.
4. Run **Mirror to Codeberg → Run workflow → main**, leaving **apply** unchecked.
   Check that the preflight and dry run succeed. The script validates destination
   syntax and nonempty credentials before any network operation; it does not
   independently certify ownership. Review destination refs separately.
5. Run again on `main` with **apply** checked. Verify the run and compare the
   destination's branch/tag commit IDs with the GitHub snapshot. A successful
   dry run alone is not evidence of a completed synchronization. Future pushes
   to `main` then apply updates automatically.

Unset `CODEBERG_MIRROR_ENABLED` (or set it to `false`) to stop future updates.
Do not rerun the old failed execution: it uses the old workflow revision and
does not exercise these safeguards. Run the corrected workflow on `main`.

## Local verification without external writes

```sh
python3 -m unittest discover -s tests -p 'test_codeberg_mirror.py' -v
python3 -m unittest discover -s tests -p 'test_workflow_boundaries.py' -v
python3 scripts/validate_workflow_boundaries.py
```

The mirror tests substitute local repositories for both HTTPS endpoints and
allow only Git's file transport inside the test wrapper. They test dry-run
immutability, multiple branches and tags, preservation of destination-only refs,
atomic rejection of divergence and configuration/credential failures. They use
dummy credentials. They do not validate real Codeberg access or modify any
external repository.
