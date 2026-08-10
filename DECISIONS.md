# Kanboard Neo — decision log

## KBN-ADR-001 — Kanboard is the human cockpit, not the source of truth

**Date:** 2026-08-09  
**Status:** Accepted

Repositories and approved local project records remain authoritative. Kanboard
presents priorities, next actions, reviews, and visible status. A Kanboard card
must link back to a stable project identifier rather than duplicate source code
or sensitive project state.

## KBN-ADR-002 — First integration phase is read-only

**Date:** 2026-08-09  
**Status:** Accepted

The first phase may validate and render a sanitized portfolio projection. It may
not create, update, move, close, or remove Kanboard projects or tasks. This keeps
the blast radius at zero while the field mapping and confidentiality rules are
verified.

## KBN-ADR-003 — Never use the application-wide JSON-RPC credential

**Date:** 2026-08-09  
**Status:** Accepted

Kanboard accepts a special `jsonrpc` username paired with the global API token.
The authorization classes apply user/project role checks only when a user
session is initialized, so this credential has a broader authority boundary than
a dedicated user. A later integration must use a dedicated account, API access
token, project membership, and a client-side procedure allowlist.

## KBN-ADR-004 — Private registry data is projected, not copied

**Date:** 2026-08-09  
**Status:** Accepted

The private registry may contain names and relationships unsuitable for a public
repository or broadly accessible dashboard. Kanboard receives only reviewed
fields such as opaque project ID, approved display name, program, status,
priority, next action, and a classification label. Absolute paths, repository
visibility details, secrets, unpublished claims, customer/player data, and
proprietary implementation details are excluded.

## KBN-ADR-005 — Machine configuration remains untracked

**Date:** 2026-08-09  
**Status:** Accepted

MCP, Botte, and Claude settings vary by machine and may reveal personal paths or
local infrastructure. The repository stores portable examples only. Generated
configuration and setup reports are ignored.
