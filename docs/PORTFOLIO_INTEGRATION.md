# Portfolio cockpit integration contract

Status: design gate — no live integration  
Last reviewed: 2026-08-09

## Purpose

Kanboard Neo is the human-facing cockpit for priorities, reviews, and next
actions. Botte Secrète holds a private portfolio index and produces deterministic
read-only validation reports. Project repositories and approved local records
remain the sources of truth.

```text
Project sources / GitHub repositories
                 |
                 v
     private Botte portfolio registry
                 |
        portfolio_sync validate/diff
                 |
        reviewed sanitized projection
                 |
                 v
       Kanboard Neo preview (read-only)
```

There is deliberately no arrow back to the registry in phase 0.

## Phase 0 — offline preview

Input is a reviewed JSON projection created outside Kanboard. The preview may be
rendered as HTML or JSON but is not inserted into the Kanboard database.

Allowed fields:

```json
{
  "project_id": "stable-opaque-id",
  "display_name": "Approved project name",
  "program": "research",
  "status": "active",
  "priority": "high",
  "next_action": "Review the validation report",
  "classification": "public|internal|restricted",
  "source_link": "optional approved URL"
}
```

Forbidden fields include credentials, absolute paths, private repository names
unless separately approved, source code, customer/player data, production
configuration, unpublished scientific claims, and proprietary Ultimate Odycer
internals.

Acceptance gate:

- schema validation passes;
- every project has a stable unique ID;
- restricted entries have an approved display name or remain opaque;
- no write-capable Kanboard API call exists in the phase-0 code path;
- preview can be reproduced from the same input.

## Phase 1 — manual import

A human reviews the phase-0 preview and explicitly selects entries to create or
update. The importer still produces a dry-run plan before any call.

Recommended mapping:

| Portfolio concept | Kanboard representation |
|---|---|
| Program | Dedicated project or category, chosen during setup |
| Project | One parent task or one Kanboard project, not both by default |
| Status | Workflow column: Triage, Backlog, Started, In Review, Done, Canceled |
| Priority | Kanboard priority plus an optional tag |
| Next action | Task title or first subtask |
| Classification | Tag and visibility rule, never a secret payload |
| Stable ID | Task `reference` such as `portfolio:<project_id>` |

Idempotency key:

```text
portfolio:<project_id>
```

Before `createTask`, the client calls `getTaskByReference` or a scoped search. A
matching task is updated only after the dry-run diff is approved. Duplicate
creation is a hard error.

## Phase 2 — constrained synchronization

This phase is not authorized by this document. It requires a separate review and
must include:

- dedicated Kanboard user, never the global `jsonrpc` credential;
- membership only in the cockpit projects it needs;
- API token stored outside repositories and logs;
- client-side allowlist initially limited to read methods;
- explicit per-run confirmation before `createTask` or `updateTask`;
- no calls to `removeProject`, `removeTask`, public-access toggles, user/group
  administration, file upload, task movement, closure, or project disablement;
- append-only audit record containing input digest, planned calls, results, and
  actor;
- retry-safe idempotency and a documented rollback procedure.

## JSON-RPC security observations

`AuthenticationMiddleware` accepts either a normal user credential/API access
token or the special username `jsonrpc` with the application token. The latter
does not initialize a user session. `UserAuthorization`, `ProjectAuthorization`,
and `TaskAuthorization` condition their role/project checks on a logged session.
Consequently, the application token must be treated as an administrative secret,
not as an integration identity.

The API surface includes destructive procedures such as `removeProject` and
`removeTask`, public-access toggles, status changes, moves, and broad project
listing. Network-level access alone is therefore insufficient protection; the
client must enforce an allowlist and the server should be exposed only through a
trusted network or authenticated reverse proxy.

## Initial read allowlist

A future client may begin with only these scoped reads after dedicated-user
permissions are proven:

```text
getMe
getMyProjectsList
getProjectById
getProjectByIdentifier
getAllTasks
getTask
getTaskByReference
searchTasks
getProjectActivity
```

The exact list must be confirmed against the installed Kanboard version. The
client fails closed on an unknown method, missing project scope, malformed
response, authentication error, or visibility mismatch.

## Operational sequence

```text
1. Validate private registry.
2. Generate sanitized projection.
3. Scan projection for forbidden keys and absolute paths.
4. Produce deterministic preview and digest.
5. Human review.
6. Optional dry-run mapping to Kanboard operations.
7. Separate approval for any write phase.
8. Record results and reconcile by stable ID.
```

## Non-goals

- replacing GitHub, local repositories, or Memory Hub;
- copying every project detail into Kanboard;
- allowing an agent to publish, deploy, merge, delete, or change production;
- exposing the private portfolio through this public repository;
- using Kanboard as a secret store.
