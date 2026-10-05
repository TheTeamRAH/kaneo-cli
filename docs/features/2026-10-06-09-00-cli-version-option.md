---
type: Feature Specification
title: Standard CLI version option
status: implemented
---

# Standard CLI version option

## Purpose

Allow deployment packaging to verify the installed Kaneo CLI version without
requiring server credentials or a running Kaneo instance.

## Scope

- Add a global `--version` option accepted before any resource command.
- Report exactly `kaneo-cli 0.1.0`, using the package's declared version.
- Preserve existing commands and global options.
- Cover the option with a CLI test and document the usage example.

## Verification requirements

- Run the complete test, lint, build, compile, help, and diff checks.
- Exercise `uv run kaneo --version` and confirm exact output.
