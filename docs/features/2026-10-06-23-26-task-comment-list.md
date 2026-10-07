---
type: Feature Specification
title: Read-only task comment listing
status: implemented
---

# Read-only task comment listing

## Purpose

Expose the comments already attached to a Kaneo task without requiring users to
fall back to a raw API request or perform a mutation.

## Scope

- Add `comment list --task-id TASK_ID --json` to the public CLI.
- Add `ApiClient.list_task_comments(task_id)` using the verified `GET
  /comment/{taskId}` route.
- Keep the operation read-only: no request body and no write-side effects.
- Cover the exact method/path and stable JSON output with the existing
  `FakeTransport` tests.
- Document the command, route, and API evidence in the README and observations.

## Settled API decision

The published Kaneo OpenAPI document at
<https://kaneo.app/docs/openapi.json> defines `GET /comment/{taskId}` as
`getTaskComments`, returning every comment for the task oldest first. The same
route also defines the existing `POST` comment-creation operation. The CLI uses
only the GET operation for this feature.

## Acceptance criteria

- `kaneo comment list --task-id TASK_ID --json` is shown in command help and
  emits compact JSON from the API response.
- The client sends exactly `GET /comment/{task_id}` with no payload or query
  parameters.
- Existing comment creation and other commands remain unchanged.
- Full tests, Ruff, package build, CLI help, and diff hygiene checks pass.

## Verification

- `uv run pytest`
- `uvx ruff check .`
- `uv build`
- `uv run kaneo --help`
- `uv run kaneo comment list --help`
- `git diff --check`
