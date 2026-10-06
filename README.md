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
uv run kaneo workspace list --json
# Only for trusted self-hosted servers using private certificates:
uv run kaneo --no-tls-verify workspace list --json
uv run kaneo project list --workspace-id WORKSPACE_ID --json
uv run kaneo task list --project-id PROJECT_ID --json
uv run kaneo task create --project-id PROJECT_ID --title "Prepare release" --status todo
uv run kaneo task update TASK_ID --status feature-review
uv run kaneo comment list --task-id TASK_ID --json
uv run kaneo comment create --task-id TASK_ID --content "Ready for review"
```

The CLI uses the server's `/api` base, bearer authentication, TLS certificate and hostname verification by default, compact stable JSON with `--json`, and actionable errors on stderr. Task creation sends `POST /task/{projectId}` with the project ID in the path, comments use `GET /comment/{taskId}` for read-only listing and `POST /comment/{taskId}` for creation. Use `--status` with a Kaneo status column slug (for example, `feature-review`); it is sent as the API `status` field. A status-only update uses Kaneo's dedicated `PUT /task/status/{taskId}` endpoint with `{"status": "..."}` and reads the task back. Updates with other fields retain the full-object update path, preserve unrelated fields, and read the task back after the update. The existing `--column-id` option remains available and is not remapped.

`workspace list` uses Kaneo's verified `GET /auth/organization/list` endpoint. The `--no-tls-verify` option is an explicit, insecure opt-in for self-hosted deployments whose private certificates are not trusted by the system; do not use it on untrusted networks. See [the API observation](docs/observations/2026-10-05-kaneo-openapi.md).

Kaneo credentials must be supplied through a private environment or secret manager; do not commit them or place them in normal command output.

## Recent Features

| Date | Purpose | Spec | Author |
| --- | --- | --- | --- |
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
