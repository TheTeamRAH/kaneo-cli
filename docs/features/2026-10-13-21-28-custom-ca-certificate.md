---
type: Feature Specification
title: Optional custom CA certificate support
status: implemented
---

# Optional custom CA certificate support

## Context

Flowforge embeds Kaneo's Python client directly and may connect to a Kaneo server
whose issuing CA is not installed in the host's default trust store. The client
currently creates a default TLS context and only offers a complete verification
bypass.

## Goal

Allow callers to add one PEM CA certificate or bundle while retaining the
platform's normal default trust roots and certificate/hostname verification.

## Settled decisions

- `HttpTransport` and `ApiClient` accept an optional `ca_cert` path.
- `client_from_environment` reads `KANEO_CA_CERT` when present and passes it to
  the client. This is the documented Flowforge deployment option.
- The custom CA is additive: `ssl.create_default_context()` remains the base and
  `load_verify_locations(cafile=ca_cert)` adds the supplied trust material.
- `verify_tls=False` remains an explicit override that disables certificate and
  hostname verification, whether or not `ca_cert` is supplied.
- `HttpTransport` and `ApiClient` accept `strict_tls`, defaulting to `True`.
  Setting it to `False` removes only `ssl.VERIFY_X509_STRICT`; CA-chain and
  hostname verification remain enabled.
- `client_from_environment` reads `KANEO_TLS_STRICT` when `strict_tls` is not
  passed explicitly. It defaults to `True` and accepts standard boolean values.
- No CLI-specific CA flag is added; the environment constructor is the stable
  deployment interface and direct library callers can pass `ca_cert` explicitly.

## Acceptance criteria

1. A supplied CA path is loaded into the default SSL context.
2. Omitted `ca_cert` preserves existing default-context behavior.
3. `verify_tls=False` results in `CERT_NONE` and disabled hostname checking.
4. `KANEO_CA_CERT` configures `client_from_environment` without exposing secret
   material in errors or output.
5. Focused and full tests, package build, compile checks, lint/format checks, and
   diff hygiene pass.
6. README and feature indexes document the environment variable and direct API
   argument, including the Flowforge dependency on the resulting version.

## Validation

Run the focused TLS/environment tests, the full pytest suite, `uv build`,
`python -m compileall src tests`, available Ruff checks, and `git diff --check`.

## Risks and out of scope

This feature does not replace the system trust store, accept certificate bytes
from environment variables, or change the insecure `verify_tls=False` behavior.
The supplied path is allowed to fail through Python's normal SSL file-loading
error so deployment mistakes are visible.
