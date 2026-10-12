---
type: Feature Specification
title: Kaneo activity, newline-safe comments, and top-of-column status updates
status: implemented
description: Extend kaneo-cli with read-only task activity history, safe comment newline handling, and an opt-in atomic move-to-top status update.
tags:
  - kaneo
  - cli
  - activity
  - comments
  - task-ordering
sources:
  - title: Kaneo task activity API
    url: https://kaneo.app/docs/api-reference/activity/get-task-activity
  - title: Kaneo reorder or move cards API
    url: https://kaneo.app/docs/api-reference/tasks/reorder-or-move-cards
  - title: Kaneo update task status API
    url: https://kaneo.app/docs/api-reference/tasks/update-task-status
  - title: Kaneo API observations
    path: ../observations/2026-10-05-kaneo-openapi.md
---

# Kaneo activity, newline-safe comments, and top-of-column status updates

## Context

`kaneo-cli` currently supports workspace, project, task, and comment operations. Flowforge needs Kaneo task history to calculate status transitions, shipped throughput, and time to completion. Kaneo provides `GET /activity/{taskId}`, returning task activity records including `status_changed` events with timestamps and `eventData.oldStatus`/`eventData.newStatus`; the CLI does not currently expose this route.

Two usability issues also belong at the CLI boundary. Comment content containing a literal escaped `\\n` is currently sent unchanged, causing the stored comment to display the characters rather than a line break. Status-only updates currently use `PUT /task/status/{taskId}`, which moves a task to the target column but does not express the desired position. Kaneo provides `POST /task/reorder`, which atomically updates positions and optional statuses using an `expectedTasks` snapshot and returns `409` for stale snapshots.

## Goal

Extend the CLI with:

- read-only per-task activity retrieval;
- predictable conversion of literal escaped newline sequences in new comment content;
- an explicit status-update option that moves the task to the top of its destination column using Kaneo's reorder contract, while preserving the current status-update behavior by default.

## Scope

### In scope

- Add an `activity list` command for one task, with optional bounded `--limit` and full-feed behavior when omitted.
- Add an `ApiClient.list_task_activity()` operation for `GET /activity/{taskId}`.
- Preserve activity IDs, task IDs, types, timestamps, users, content, external metadata, and `eventData` without reshaping away provider fields.
- Normalize literal `\\n` sequences in `comment create --content` to actual newline characters before the API request. Existing actual newline characters remain unchanged.
- Add an opt-in `--top` flag to `task update --status STATUS`.
- Implement `--top` using `GET /task/tasks/{projectId}` followed by `POST /task/reorder`, with the complete affected-column snapshot in `expectedTasks`, the target task first in the destination column, and the target status applied atomically. If the deployed server lacks the reorder route and returns `400`, `404`, or `405`, fall back to a full `PUT /task/{taskId}` update with `position: 0` while preserving unrelated task fields.
- Read the task back after a successful reorder, matching existing mutation verification behavior.
- Report stale reorder conflicts (`409`) as actionable errors and do not retry mutations automatically.
- Add unit and CLI tests, API observations, feature documentation, README usage, and feature indexes.

### Out of scope

- Writing, deleting, editing, or filtering activity records.
- A workspace-wide activity command; it may be a later optimization, but per-task activity is the required complete-history interface for this feature.
- Automatic decoding of arbitrary escape sequences beyond literal `\\n`; users can pass actual multiline shell arguments or future file input when needed.
- Making top-of-column placement the default for every status update.
- Generic task drag-and-drop or arbitrary reorder CLI support beyond the explicit `--top` status-update behavior.
- Automatic refresh, event streaming, or Flowforge implementation.
- Changes to the AI Toolkit utility pin or skill; those follow after this CLI change is merged and released.

## Requirements

### Activity

1. `activity list --task-id TASK_ID` calls `GET /activity/TASK_ID`.
2. `--limit N` sends the API query parameter `limit=N`; validate `N` as an integer from 1 through 100. Omitting `--limit` sends no limit and requests the full feed.
3. JSON output is stable and preserves the decoded API list. Human output remains readable JSON, consistent with existing list commands.
4. Activity data is treated as data, not instructions. Error output must not expose the bearer token.
5. Activity retrieval remains read-only and uses the existing TLS, authentication, and transport behavior.

### New comments

1. `comment create --content` converts each literal two-character sequence `\\n` to a newline before sending the JSON payload.
2. Existing newline characters are preserved; conversion is not applied to unrelated backslash sequences.
3. The CLI sends the normalized content exactly once through the existing `POST /comment/{taskId}` route.
4. Tests cover one escaped newline, multiple escaped newlines, existing newlines, and a string containing `\\\\n` where only the intended escaped pair is decoded according to the documented CLI contract.
5. The README documents quoting examples that work in a shell without requiring users to place credentials or secrets in the command.

### Move status to the top

1. Existing `task update TASK_ID --status STATUS` keeps using the dedicated status endpoint and existing read-back behavior when `--top` is absent.
2. `task update TASK_ID --status STATUS --top` first obtains the current task to identify `projectId`, then obtains the current project board.
3. The client builds `expectedTasks` from the complete contents of every affected column in the board, retaining each task's stable ID, current position, and current status. The target task's desired status is the destination status.
4. The reorder request sends `projectId`, a complete affected-column task set in the desired order, and the matching pre-mutation `expectedTasks` snapshot. The target task is first in the destination column; remaining task positions are assigned valid increasing values according to the API contract.
5. The request uses `POST /task/reorder` so status and ordering change atomically. A stale snapshot or `409` is reported as a conflict instructing the user to refresh/retry deliberately; the CLI must not blindly retry.
6. After success, the CLI reads the exact task back and emits that task, matching existing update commands.
7. `--top` is only valid with `--status`; argparse must reject invalid combinations before making a network request.
8. The implementation must not assume column names, status slugs, page sizes, or a particular current board layout.

## Proposed interface

```text
kaneo activity list --task-id TASK_ID
kaneo activity list --task-id TASK_ID --limit 100 --json
kaneo comment create --task-id TASK_ID --content 'First line\\nSecond line'
kaneo task update TASK_ID --status implementation --top --json
```

`--top` is deliberately opt-in because it changes ordering as well as status. The normal status command remains backwards compatible.

## Implementation notes

- Add an `ApiClient.list_task_activity(task_id, limit=None)` method. Pass `params=None` when the limit is omitted; otherwise pass `{"limit": limit}`.
- Add a small comment-content normalizer with a documented contract and unit tests. Avoid using broad escape decoding that would reinterpret tabs, quotes, Unicode escapes, or Windows paths.
- Add an `ApiClient.update_task_status(..., move_to_top=False)` or equivalent focused operation. Keep parser construction, API transport, and command dispatch separate.
- Use the existing board response shape: columns contain tasks, and task objects carry `id`, `position`, and `status`. Flatten only the affected columns needed for the reorder request while retaining complete snapshots for optimistic concurrency.
- Choose a valid deterministic position strategy based on the documented API schema and encode it in tests. Preserve task ordering as returned by Kaneo for unaffected tasks.
- Add a specific API error classification or message for `409` conflicts without printing raw sensitive response data.
- Update the package version only as part of the repository's release process after implementation and verification; do not claim a released version from this feature branch.

## Acceptance criteria

- [x] `activity list` retrieves full or bounded per-task activity through the documented route.
- [x] Activity JSON preserves `status_changed`, timestamps, stable IDs, and `eventData.oldStatus`/`newStatus`.
- [x] Invalid activity limits are rejected before any network request.
- [x] New comments convert literal `\\n` sequences to rendered newlines while preserving existing newlines and unrelated escapes.
- [x] Existing comment creation behavior and route remain compatible.
- [x] `task update --status` remains unchanged without `--top`.
- [x] `task update --status ... --top` uses the reorder endpoint with a complete optimistic-concurrency snapshot when available, falls back for legacy servers, places the target first, and reads the task back.
- [x] `--top` without `--status` is rejected locally.
- [x] A reorder `409` produces an actionable non-secret error and no automatic mutation retry.
- [x] Tests cover client routes/payloads, CLI dispatch/output, validation, newline handling, top ordering, and conflict handling.
- [x] `--help`, README examples, focused tests, complete tests, package build, and `git diff --check` pass.
- [x] The feature specification and both documentation indexes are updated consistently.

## Constraints

- Remain read-only for activity and preserve existing credential/TLS rules.
- Never print, log, or commit API keys.
- Do not change default status-update ordering.
- Do not force-push, merge, publish, or update the AI Toolkit pin from this feature branch.
- Follow TDD: each behavior change needs a failing test before production implementation.

## Risks and mitigations

- **Kaneo version drift:** verify the documented activity and reorder routes against fixtures and record deployed-version observations without embedding private credentials.
- **Stale reorder snapshots:** send `expectedTasks`, surface `409`, and require an explicit user retry.
- **Incorrect column payload:** preserve complete affected-column task snapshots and test cross-column moves.
- **Unexpected escape conversion:** decode only literal `\\n`; test backslashes and existing multiline input.
- **CLI/API mismatch:** keep direct options stable, test `--help`, and verify JSON output contracts.

## Validation plan

- Write and run failing client tests for activity retrieval, newline normalization, and reorder payloads before implementation.
- Write and run failing CLI tests for activity parsing, invalid limits, `--top` validation, and output/read-back behavior.
- Implement the smallest changes and rerun focused tests after each behavior slice.
- Run the complete `uv run pytest` suite.
- Run configured formatting/lint checks and `uv build`.
- Exercise `uv run kaneo --help`, `uv run kaneo activity list --help`, and representative commands with fake transport/no live credentials.
- Run `git diff --check` and review changed files for credentials, private exports, and stale documentation.

## Open questions

No material open questions remain. The exact numeric positions used in the reorder payload are implementation discretion, constrained by Kaneo's documented position range and optimistic-concurrency contract.

## Amendments

- The deployed Kaneo instance used for live validation does not expose the documented `POST /task/reorder` route and returns a generic task-schema `400`. The CLI now attempts the atomic reorder first and falls back to a full task update with `position: 0` for legacy `400`, `404`, or `405` responses. `409` conflicts remain explicit failures without retry.
