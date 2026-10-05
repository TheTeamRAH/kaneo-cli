# Kaneo API observations

Verified against the published OpenAPI document at
<https://kaneo.app/docs/openapi.json> on 2026-10-05:

- Task creation is `POST /task/{projectId}`. The project ID is a path
  parameter, not a `projectId` property in the request body.
- Task comment creation is `POST /comment/{taskId}`, with the comment content
  in the request body.
- The published document includes `GET /user/me`, but it does not include an
  obvious documented `GET /workspace` collection route.

The CLI retains `workspace list` as a documented compatibility assumption that
calls `GET /workspace` for Kaneo deployments exposing that route. It does not
claim that route is part of the published OpenAPI contract; failures from a
deployment without the route are reported by the normal API error handling.
