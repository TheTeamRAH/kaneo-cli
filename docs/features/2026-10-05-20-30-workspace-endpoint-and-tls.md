---
type: Feature Specification
title: Workspace endpoint and explicit TLS bypass
status: implemented
---

# Workspace endpoint and explicit TLS bypass

## Purpose

Use the verified Kaneo organization-list endpoint for workspace discovery and
support self-hosted deployments with private certificates without weakening the
normal TLS defaults.

## Scope

- Call `GET /auth/organization/list` for `workspace list`.
- Verify TLS certificates and hostnames by default in the urllib transport.
- Add the explicit `--no-tls-verify` CLI opt-in for trusted private-certificate deployments.
- Keep API keys and other secrets out of output.

## Safety

`--no-tls-verify` is intentionally prominent and insecure. It must never be
enabled by an environment variable or silently selected; users should prefer
installing the deployment's CA certificate in the system trust store.

## Verification requirements

- Test the exact workspace method and path.
- Test default TLS verification and the explicit opt-out SSL context.
- Test CLI flag propagation and help text.
- Run the complete test, lint, build, compile, help, and diff checks.
