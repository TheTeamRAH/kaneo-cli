# kaneo-cli

A direct, scriptable Python CLI for managing workspaces, projects, tasks, and task comments in a self-hosted Kaneo instance. It uses Kaneo's HTTP API on demand and does not require MCP.

## Repo Structure

```text
.
├── src/kaneo_cli/  # client and argparse CLI
├── tests/          # fake-transport tests
└── docs/features/  # feature specifications
```

## Getting Started

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run kaneo --version
export KANEO_API_URL="https://kaneo.example"  # optional; defaults to http://localhost:1337
export KANEO_API_KEY="..."                    # keep this private
export KANEO_CA_CERT="/run/secrets/kaneo-ca.pem"  # optional additive PEM CA bundle
uv run kaneo workspace list --json
# Only for trusted self-hosted servers using private certificates:
uv run kaneo --no-tls-verify workspace list --json
uv run kaneo project list --workspace-id WORKSPACE_ID --json
uv run kaneo task list --project-id PROJECT_ID --json
uv run kaneo task create --project-id PROJECT_ID --title "Prepare release" --status todo
uv run kaneo task update TASK_ID --status feature-review
uv run kaneo task update TASK_ID --status feature-review --top
uv run kaneo comment list --task-id TASK_ID --json
uv run kaneo comment create --task-id TASK_ID --content "First line\\nSecond line"
uv run kaneo activity list --task-id TASK_ID --json
```

The CLI uses the server's `/api` base, bearer authentication, TLS certificate and hostname verification by default, compact stable JSON with `--json`, and actionable errors on stderr. Task creation sends `POST /task/{projectId}` with the project ID in the path, comments use `GET /comment/{taskId}` for read-only listing and `POST /comment/{taskId}` for creation. Literal `\\n` sequences in new comment content are converted to rendered newlines. Use `--status` with a Kaneo status column slug (for example, `feature-review`); it is sent as the API `status` field. A status-only update uses Kaneo's dedicated `PUT /task/status/{taskId}` endpoint with `{"status": "..."}` and reads the task back. Add `--top` to a status update to use Kaneo's optimistic-concurrency reorder endpoint and place the task first in the destination column. Updates with other fields retain the full-object update path, preserve unrelated fields, and read the task back after the update. `activity list` reads the per-task activity feed; omit `--limit` for the full feed or use a value from 1 through 100. The existing `--column-id` option remains available and is not remapped.

`workspace list` uses Kaneo's verified `GET /auth/organization/list` endpoint. Set `KANEO_CA_CERT` to a PEM certificate or bundle path when a self-hosted CA is not in the platform trust store; it is added to the normal default trust roots, so verification remains enabled. Flowforge can instead pass `ca_cert="/path/to/ca.pem"` directly to `ApiClient` or `client_from_environment`. The `--no-tls-verify` option is an explicit, insecure opt-in for self-hosted deployments whose private certificates are not trusted by the system; do not use it on untrusted networks. See [the API observation](docs/observations/2026-10-05-kaneo-openapi.md).

Kaneo credentials must be supplied through a private environment or secret manager; do not commit them or place them in normal command output.

## Recent Features

| Date | Purpose | Spec | Author |
| --- | --- | --- | --- |
| 2026-10-13-21-28 | Add additive custom CA support for direct library use and `KANEO_CA_CERT` deployments | [Custom CA certificate](docs/features/2026-10-13-21-28-custom-ca-certificate.md) | whose-footprints-are-these |
| 2026-10-12-19-44 | Add task activity retrieval, newline-safe comments, and opt-in top-of-column status updates | [Activity, comments, and status order](docs/features/2026-10-12-19-44-activity-comments-status-order.md) | whose-footprints-are-these |
| 2026-10-06-23-26 | Add read-only task comment listing through the verified GET comment route | [Task comment list](docs/features/2026-10-06-23-26-task-comment-list.md) | whose-footprints-are-these |
| 2026-10-06-09-00 | Add standard `--version` output for deployment verification | [CLI version option](docs/features/2026-10-06-09-00-cli-version-option.md) | whose-footprints-are-these |
| 2026-10-05-21-00 | Add explicit task status option for Kaneo task mutations | [Explicit task status option](docs/features/2026-10-05-21-00-task-status-option.md) | whose-footprints-are-these |
| 2026-10-05-20-30 | Correct workspace discovery and add explicit opt-in TLS bypass | [Workspace endpoint and TLS](docs/features/2026-10-05-20-30-workspace-endpoint-and-tls.md) | whose-footprints-are-these |
| 2026-10-05-19-10 | Direct CLI for workspaces, projects, tasks, and comments | [Kaneo CLI bootstrap](docs/features/2026-10-05-19-10-kaneo-cli-bootstrap.md) | whose-footprints-are-these |

See [the complete feature index](docs/features/README.md).

## Contributing

This is an AI-first development repository. Point your agent or model at [AGENTS.md](AGENTS.md) before contributing.

- Create and review a feature specification before implementation.
- Use focused branches and keep implementation, tests, and documentation together.
- Follow the Python, CLI, credential-safety, and validation conventions in `AGENTS.md`.
- Keep feature indexes and verified usage documentation current.
