# AGENTS.md

## Purpose and scope

`kaneo-cli` is a public, Python-based command-line client for a self-hosted Kaneo server. It provides explicit, scriptable operations for workspaces, projects, tasks, and task comments through Kaneo's HTTP API. MCP is deliberately out of scope for this repository; the CLI is the direct, on-demand integration boundary.

## Repository workflow

- Start implementation from an up-to-date `main` branch.
- Use focused branches named `<type>/<purpose>`, normally `feature/<purpose>` or `fix/<purpose>`.
- Create or update a feature specification under `docs/features/` before implementation.
- Keep implementation, tests, and directly related documentation together on the focused branch.
- Do not merge directly to `main` or force-push.
- Use the Git identity configured for this repository; the expected default is `whose-footprints-are-these <huh.whose.footprints.are.these@gmail.com>`.

## Documentation conventions

- Maintain `docs/features/README.md` as the complete feature index.
- Keep the root README's Recent Features table capped at the ten newest implemented features; keep all specifications in the complete index.
- Feature and debugging filenames use `YYYY-MM-DD-HH-MM` followed by a descriptive slug.
- Record durable API discoveries in `docs/observations/` and troubleshooting/root-cause findings in `docs/debugging/`.
- Keep README commands verified against the current repository.

## Python and CLI conventions

- Use `pyproject.toml` and `uv`; prefer `uv run` for project commands.
- Follow TDD: establish a failing test, implement the smallest useful change, then refactor after green tests.
- Use typed, small functions and Google-style docstrings for public interfaces and important helpers.
- Use `argparse` subcommands with singular resource namespaces and explicit verbs, such as `workspace list`, `project list`, `task create`, and `task update`.
- Keep parser construction, transport/API code, and command handlers separate.
- Provide stable human-readable output plus `--json` machine-readable output.
- Read credentials from approved environment/configuration mechanisms; never commit secrets or print authorization material.
- Validate inputs at the CLI boundary and expose actionable errors without sensitive response data.
- For updates, preserve unrelated fields when the server requires full-object payloads and read back the exact resource when supported.

## Validation and definition of done

A change is complete only when:

- Focused and full tests pass.
- Formatting, linting, and package-build checks pass when configured.
- `--help` and representative CLI smoke tests work.
- Documentation and feature indexes are updated.
- `git diff --check` passes.
- Public-repository contents contain no credentials, private exports, caches, or host-specific state.
- The branch, commit, remote, and working-tree state have been verified before handoff.

## Proposed initial layout

```text
src/kaneo_cli/    Python package, CLI parser, API client, and output handling
tests/            Unit and CLI tests
docs/features/    Feature specifications and complete index
docs/observations/ Durable API and integration discoveries
```

The layout above is proposed until implementation establishes the files. Do not claim a command or check exists until it has been exercised.
