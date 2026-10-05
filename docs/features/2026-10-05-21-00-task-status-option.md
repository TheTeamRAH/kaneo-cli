---
type: Feature Specification
title: Explicit task status option
status: implemented
---

# Explicit task status option

## Purpose

Allow users to move a Kaneo task by its status column slug, including the
`feature-review` status required by the task update API.

## Scope

- Add `--status` to `task create` and `task update`.
- Send the option as the Kaneo API `status` payload field.
- Preserve the existing `--column-id` option without remapping it.
- Cover create and update payloads with focused CLI tests.

## Verification requirements

- Assert that `--status feature-review` is sent as `status: feature-review`.
- Run the complete test, lint, build, compile, help, and diff checks.
