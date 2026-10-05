# kaneo-cli

A direct, scriptable Python CLI for managing workspaces, projects, tasks, and task comments in a self-hosted Kaneo instance. It uses Kaneo's HTTP API on demand and does not require MCP.

## Repo Structure

```text
.
├── AGENTS.md
├── docs/
│   └── features/
├── README.md
└── .gitignore
```

## Getting Started

Implementation is currently being bootstrapped. The intended setup and usage commands will be added only after they are implemented and exercised.

Kaneo credentials must be supplied through a private environment or secret manager; do not commit them or place them in normal command output.

## Recent Features

| Date | Purpose | Spec | Author |
| --- | --- | --- | --- |

No implemented features are recorded yet.

See [the complete feature index](docs/features/README.md).

## Contributing

This is an AI-first development repository. Point your agent or model at [AGENTS.md](AGENTS.md) before contributing.

- Create and review a feature specification before implementation.
- Use focused branches and keep implementation, tests, and documentation together.
- Follow the Python, CLI, credential-safety, and validation conventions in `AGENTS.md`.
- Keep feature indexes and verified usage documentation current.
