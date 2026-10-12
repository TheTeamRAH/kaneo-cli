# Kaneo API observations

Verified against the published OpenAPI document at
<https://kaneo.app/docs/openapi.json> on 2026-10-05:

- Task creation is `POST /task/{projectId}`. The project ID is a path
  parameter, not a `projectId` property in the request body.
- Task comment listing is `GET /comment/{taskId}`, returning every comment
  oldest first with author information. The same route's `POST` operation
  creates a comment with content in the request body.
- Status-only task updates use `PUT /task/status/{taskId}` with a JSON body of
  `{"status": "..."}`. The generic task update route is reserved for full
  task-object updates; the CLI reads the task back after either mutation.
- Workspace discovery was verified against the TeamRAH Kaneo deployment as
  `GET /auth/organization/list`; it returned the real TeamRAH workspace.
- The published activity API provides `GET /activity/{taskId}` for a full task
  feed or a bounded `limit` from 1 through 100. Status changes are returned as
  `status_changed` records with `createdAt` and `eventData.oldStatus`/
  `eventData.newStatus`.
- The published reorder API provides `POST /task/reorder` with `projectId`,
  desired `tasks`, and `expectedTasks`; stale snapshots return `409`. This is
  the API contract used by the CLI's opt-in move-to-top status update.

The CLI's `workspace list` calls `GET /auth/organization/list`. The published
OpenAPI document includes `GET /user/me`, but it does not describe this
deployment-specific organization listing route. The client continues to report
deployment failures through its normal API error handling.

TLS certificate and hostname verification remain enabled by default. The CLI
supports the explicit `--no-tls-verify` opt-in for trusted self-hosted
deployments using private certificates; this bypass must not be treated as the
normal or safe configuration.
