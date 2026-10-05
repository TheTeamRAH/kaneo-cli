---
type: Feature Specification
title: Kaneo CLI bootstrap
status: proposed
---

# Kaneo CLI bootstrap

## Purpose

Create a public Python CLI for interacting with a self-hosted Kaneo server through its documented HTTP API. The initial scope covers workspace, project, task, and task-comment workflows without requiring MCP to be enabled in an agent session.

## Scope

- List accessible workspaces.
- List projects in a workspace.
- List tasks in a project.
- Create and update tasks.
- Add comments to tasks.
- Support authenticated self-hosted Kaneo API URLs and machine-readable JSON output.
- Keep credentials out of source, arguments where avoidable, fixtures, and normal output.

## Out of scope

- MCP server implementation or configuration.
- Labels, relations, time entries, notifications, and user administration.
- Destructive task deletion unless separately specified.
- Assumptions about a particular Kaneo deployment's host or data.

## Acceptance criteria

- The package installs with `uv` and exposes a documented executable.
- Commands use explicit resource namespaces and verbs.
- API requests use bearer authentication and actionable error handling.
- Read and mutation commands have automated tests using a fake transport.
- JSON output is stable enough for scripts and agents.
- README usage examples are exercised locally.

## Safety and compatibility

- API keys are read from an environment variable or an explicitly supported private configuration mechanism.
- Mutation commands validate required identifiers and fields before sending requests.
- Successful mutations are read back where the API contract permits, avoiding blind retries.
- The client must not print authorization headers or secret values.

## Verification requirements

- Run the focused and full test suites.
- Run lint/format checks configured by the repository.
- Run package build validation.
- Exercise `--help` and representative commands against the fake transport.
- Run `git diff --check` and inspect the final public-repository contents for secrets.
