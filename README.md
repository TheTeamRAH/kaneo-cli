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
export KANEO_API_URL="https://kaneo.example"  # optional; defaults to http://localhost:1337
export KANEO_API_KEY="..."                    # keep this private
uv run kaneo workspace list --json
uv run kaneo project list --workspace-id WORKSPACE_ID --json
uv run kaneo task list --project-id PROJECT_ID --json
uv run kaneo task create --project-id PROJECT_ID --title "Prepare release"
uv run kaneo task update TASK_ID --title "Release candidate"
uv run kaneo comment create --task-id TASK_ID --content "Ready for review"
```

The CLI uses the server's `/api` base, bearer authentication, compact stable JSON with `--json`, and actionable errors on stderr. Task updates read the existing task, preserve unrelated fields, and read it back after the update.

Kaneo credentials must be supplied through a private environment or secret manager; do not commit them or place them in normal command output.

## Recent Features

| Date | Purpose | Spec | Author |
| --- | --- | --- | --- |
| 2026-10-05-19-10 | Direct CLI for workspaces, projects, tasks, and comments | [Kaneo CLI bootstrap](docs/features/2026-10-05-19-10-kaneo-cli-bootstrap.md) | whose-footprints-are-these |

See [the complete feature index](docs/features/README.md).

## Contributing

This is an AI-first development repository. Point your agent or model at [AGENTS.md](AGENTS.md) before contributing.

- Create and review a feature specification before implementation.
- Use focused branches and keep implementation, tests, and documentation together.
- Follow the Python, CLI, credential-safety, and validation conventions in `AGENTS.md`.
- Keep feature indexes and verified usage documentation current.
